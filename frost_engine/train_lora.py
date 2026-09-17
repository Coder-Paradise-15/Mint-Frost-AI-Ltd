"""Fine-tune Frost-V1 with 4-bit LoRA and optionally export a GGUF model.

Training requires a CUDA-enabled environment with the optional ML dependencies.
A 16GB CPU-only Codespace can generate data and serve GGUF, but is not a
practical environment for QLoRA training.
"""

import argparse
import shutil
import subprocess
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--dataset", type=Path, default=Path("frost_engine/frost_v1_dataset.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/frost-v1-lora"))
    parser.add_argument("--gguf-output", type=Path, default=Path("artifacts/frost-v1-q4_k_m.gguf"))
    parser.add_argument("--llama-cpp-dir", type=Path, default=None, help="Directory containing convert_hf_to_gguf.py and llama-quantize")
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--skip-gguf", action="store_true")
    return parser.parse_args()


def format_messages(messages, tokenizer):
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return "\n".join(f"{message['role'].capitalize()}: {message['content']}" for message in messages)


def export_gguf(merged_dir, output_path, llama_cpp_dir):
    converter = llama_cpp_dir / "convert_hf_to_gguf.py" if llama_cpp_dir else Path("convert_hf_to_gguf.py")
    quantizer = llama_cpp_dir / "llama-quantize" if llama_cpp_dir else Path("llama-quantize")
    if not converter.exists() or not quantizer.exists():
        raise FileNotFoundError(
            "GGUF export needs llama.cpp's convert_hf_to_gguf.py and llama-quantize; "
            "pass --llama-cpp-dir or use --skip-gguf"
        )
    f16_path = output_path.with_name(f"{output_path.stem}-f16.gguf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python", str(converter), str(merged_dir), "--outfile", str(f16_path), "--outtype", "f16"], check=True)
    subprocess.run([str(quantizer), str(f16_path), str(output_path), "Q4_K_M"], check=True)
    f16_path.unlink(missing_ok=True)


def main():
    args = parse_args()
    if not args.dataset.exists():
        raise FileNotFoundError(f"Dataset not found: {args.dataset}. Run generate_dataset.py first.")

    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                                  DataCollatorForLanguageModeling, Trainer, TrainingArguments)
    except ImportError as exc:
        raise SystemExit(
            "Install training extras first: pip install torch transformers datasets peft "
            "accelerate bitsandbytes\n"
            f"Missing dependency: {exc}"
        ) from exc

    if not torch.cuda.is_available():
        raise SystemExit("QLoRA requires CUDA. This 16GB CPU-only Codespace can run inference, but not practical 7B 4-bit training.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quant_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(args.base_model, quantization_config=quant_config, device_map="auto")
    model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    ))
    model.print_trainable_parameters()

    dataset = load_dataset("json", data_files=str(args.dataset), split="train")
    dataset = dataset.map(lambda row: {"text": format_messages(row["messages"], tokenizer)}, remove_columns=dataset.column_names)
    dataset = dataset.map(lambda row: tokenizer(row["text"], truncation=True, max_length=args.max_length), batched=False)
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(args.output_dir), num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size, gradient_accumulation_steps=args.gradient_accumulation,
            learning_rate=args.learning_rate, logging_steps=5, save_strategy="epoch",
            fp16=True, report_to="none", optim="paged_adamw_8bit",
        ),
        train_dataset=dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    adapter_dir = args.output_dir / "adapter"
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

    if args.skip_gguf:
        print(f"Saved LoRA adapter to {adapter_dir}")
        return
    merged_dir = args.output_dir / "merged"
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained(merged_dir, safe_serialization=True)
    tokenizer.save_pretrained(merged_dir)
    export_gguf(merged_dir, args.gguf_output, args.llama_cpp_dir)
    print(f"Exported {args.gguf_output}")


if __name__ == "__main__":
    main()
