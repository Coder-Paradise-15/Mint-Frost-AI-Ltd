/* Mint Frost AI - Analytics Controller v2 */
(function () {
  'use strict';
  let charts = {};
  const C = { mint:'#37e6b5',cyan:'#00d2ff',red:'#ff3838',orange:'#ff8225',yellow:'#f1c40f',green:'#2ecc71',purple:'#9b59b6',blue:'#3498db' };
  const PIE = [C.mint,C.orange,C.red,C.cyan,C.yellow,C.purple,C.blue];

  function kill(id){ if(charts[id]){charts[id].destroy();delete charts[id];} }

  function bar(id,labels,values,color){
    kill(id);
    const ctx=document.getElementById(id); if(!ctx)return;
    charts[id]=new Chart(ctx,{type:'bar',data:{labels,datasets:[{data:values,backgroundColor:color+'44',borderColor:color,borderWidth:2,borderRadius:8,hoverBackgroundColor:color+'88'}]},options:{responsive:true,animation:{duration:800,easing:'easeOutQuart'},plugins:{legend:{display:false},tooltip:{backgroundColor:'rgba(15,22,34,0.95)',titleColor:'#37e6b5',bodyColor:'rgba(255,255,255,0.8)',borderColor:'rgba(55,230,181,0.3)',borderWidth:1}},scales:{x:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'rgba(255,255,255,0.45)',font:{size:11}}},y:{beginAtZero:true,grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'rgba(255,255,255,0.45)',font:{size:11},stepSize:1}}}}});
  }

  function donut(id,labels,values){
    kill(id);
    const ctx=document.getElementById(id); if(!ctx)return;
    charts[id]=new Chart(ctx,{type:'doughnut',data:{labels,datasets:[{data:values,backgroundColor:PIE.slice(0,values.length).map(c=>c+'cc'),borderColor:PIE.slice(0,values.length),borderWidth:2,hoverOffset:6}]},options:{responsive:true,cutout:'68%',animation:{duration:800,easing:'easeOutQuart'},plugins:{legend:{position:'bottom',labels:{color:'rgba(255,255,255,0.55)',font:{size:10},padding:8,boxWidth:10}},tooltip:{backgroundColor:'rgba(15,22,34,0.95)',titleColor:'#37e6b5',bodyColor:'rgba(255,255,255,0.8)',borderColor:'rgba(55,230,181,0.3)',borderWidth:1}}}});
  }

  function row(label,val,icon,color){
    const c=color||'var(--mint)';
    return `<div style="display:flex;justify-content:space-between;align-items:center;padding:11px 14px;background:rgba(255,255,255,0.03);border-radius:10px;font-size:13px;border:1px solid rgba(255,255,255,0.05);transition:background 0.2s;" onmouseover="this.style.background='rgba(55,230,181,0.06)'" onmouseout="this.style.background='rgba(255,255,255,0.03)'"><span style="color:rgba(255,255,255,0.6);display:flex;align-items:center;gap:8px;"><i class="fas fa-${icon}" style="color:${c};width:14px;"></i>${label}</span><span style="font-weight:700;color:#fff;font-size:13px;">${val}</span></div>`;
  }

  function insight(text,i){
    const configs=[
      {icon:'bolt',bg:'rgba(55,230,181,0.06)',border:'rgba(55,230,181,0.2)',ic:'#37e6b5'},
      {icon:'chart-line',bg:'rgba(0,210,255,0.06)',border:'rgba(0,210,255,0.2)',ic:'#00d2ff'},
      {icon:'exclamation-triangle',bg:'rgba(255,130,37,0.06)',border:'rgba(255,130,37,0.2)',ic:'#ff8225'},
      {icon:'star',bg:'rgba(241,196,15,0.06)',border:'rgba(241,196,15,0.2)',ic:'#f1c40f'},
      {icon:'rocket',bg:'rgba(155,89,182,0.06)',border:'rgba(155,89,182,0.2)',ic:'#9b59b6'},
      {icon:'fire',bg:'rgba(255,56,56,0.06)',border:'rgba(255,56,56,0.2)',ic:'#ff3838'},
    ];
    const cfg=configs[i%configs.length];
    return `<div style="display:flex;align-items:flex-start;gap:12px;padding:14px 16px;background:${cfg.bg};border:1px solid ${cfg.border};border-radius:12px;font-size:13px;line-height:1.6;color:rgba(255,255,255,0.88);transition:transform 0.2s,box-shadow 0.2s;" onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 4px 16px rgba(0,0,0,0.3)'" onmouseout="this.style.transform='';this.style.boxShadow=''"><i class="fas fa-${cfg.icon}" style="color:${cfg.ic};margin-top:2px;flex-shrink:0;font-size:14px;"></i><span>${text}</span></div>`;
  }

  function scoreRing(score){
    const el=document.getElementById('an-score-ring');
    if(!el)return;
    const pct=Math.max(0,Math.min(100,score));
    const color=pct>=70?C.mint:pct>=40?C.orange:C.red;
    const dash=Math.round(pct*2.51);
    el.innerHTML=`<svg viewBox="0 0 100 100" style="width:100%;height:100%;transform:rotate(-90deg)">
      <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8"/>
      <circle cx="50" cy="50" r="40" fill="none" stroke="${color}" stroke-width="8"
        stroke-dasharray="${dash} 251" stroke-linecap="round"
        style="transition:stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1);filter:drop-shadow(0 0 6px ${color}88)"/>
    </svg>
    <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
      <span style="font-size:22px;font-weight:800;color:#fff;">${pct}</span>
      <span style="font-size:9px;color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:1px;">Score</span>
    </div>`;
  }

  function coachBanner(coach){
    const el=document.getElementById('an-coach-banner');
    if(!el||!coach)return;
    const riskColor={'LOW':C.mint,'MEDIUM':C.orange,'HIGH':C.red,'CRITICAL':'#ff0055'}[coach.overall_risk||'LOW']||C.mint;
    el.innerHTML=`
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,var(--mint),#00d2ff);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">🤖</div>
        <div>
          <div style="font-size:14px;font-weight:700;color:#fff;">${coach.greeting||'Hello!'}</div>
          <div style="font-size:11px;color:rgba(255,255,255,0.45);">AI Productivity Coach • Live Analysis</div>
        </div>
        <div style="margin-left:auto;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:700;background:${riskColor}22;color:${riskColor};border:1px solid ${riskColor}44;">${coach.overall_risk||'ANALYZING'}</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
        <div style="padding:12px;background:rgba(255,255,255,0.03);border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
          <div style="font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;"><i class="fas fa-crosshairs" style="color:var(--mint);margin-right:4px;"></i>Current Focus</div>
          <div style="font-size:13px;font-weight:600;color:#fff;">${coach.current_focus||'—'}</div>
        </div>
        <div style="padding:12px;background:rgba(255,255,255,0.03);border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
          <div style="font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;"><i class="fas fa-clock" style="color:#ff8225;margin-right:4px;"></i>Finish ETA</div>
          <div style="font-size:13px;font-weight:600;color:#fff;">${coach.estimated_finish_time||'—'}</div>
        </div>
      </div>
      <div style="padding:12px 14px;background:rgba(55,230,181,0.05);border:1px solid rgba(55,230,181,0.15);border-radius:10px;font-size:13px;color:rgba(255,255,255,0.85);line-height:1.5;">
        <i class="fas fa-lightbulb" style="color:var(--mint);margin-right:8px;"></i>${coach.top_recommendation||coach.today_motivation||'Keep going!'}
      </div>`;
  }

  window.loadAnalytics = async function(){
    // Show loading pulse on stat cards
    document.querySelectorAll('.an-stat-val').forEach(el=>el.style.opacity='0.4');
    try{
      const [res, coachRes] = await Promise.all([
        fetch('/api/analytics/data'),
        fetch('/api/coach/analyze').catch(()=>null)
      ]);
      const d=await res.json();
      if(!d.success) return;
      const s=d.stats;
      const set=(id,v)=>{const el=document.getElementById(id);if(el){el.textContent=v;el.style.opacity='1';}};
      set('an-total',s.total);
      set('an-completed',s.completed);
      set('an-pending',s.pending);
      set('an-overdue',s.overdue);
      set('an-rate',s.completion_rate+'%');
      set('an-score',s.productivity_score+'/100');
      set('an-score-label',s.score_label+' 🏆');
      set('an-streak',s.streak+' days');
      scoreRing(s.productivity_score);

      // Color overdue red if > 0
      const ovEl=document.getElementById('an-overdue');
      if(ovEl) ovEl.style.color=s.overdue>0?'#ff3838':'#37e6b5';

      bar('chart-daily',d.charts.daily.labels,d.charts.daily.values,C.mint);
      bar('chart-weekly',d.charts.weekly.labels,d.charts.weekly.values,C.cyan);
      donut('chart-risk',d.charts.risk.labels,d.charts.risk.values);
      donut('chart-priority',d.charts.priority.labels,d.charts.priority.values);
      donut('chart-category',d.charts.category.labels,d.charts.category.values);

      const t=d.trends;
      const tEl=document.getElementById('an-trends');
      if(tEl) tEl.innerHTML=
        row('Most Productive Day',t.most_productive,'sun',C.yellow)+
        row('Least Productive Day',t.least_productive,'moon','rgba(255,255,255,0.4)')+
        row('Avg Overdue Rate',t.avg_overdue_rate+'%','exclamation-triangle',t.avg_overdue_rate>20?C.red:C.orange);

      const p=d.predictions;
      const pEl=document.getElementById('an-predictions');
      if(pEl) pEl.innerHTML=
        row('Tomorrow Task Load',p.tomorrow_load+' tasks','tasks',C.cyan)+
        row('Tomorrow Risk Level',p.tomorrow_risk,'fire',p.tomorrow_risk==='High'?C.red:C.orange)+
        row('Expected Completion',p.expected_completion+'%','check-circle',C.mint)+
        row('Planner Success Rate',p.expected_planner_success+'%','magic',C.purple);

      const iEl=document.getElementById('an-insights');
      if(iEl&&d.insights&&d.insights.length)
        iEl.innerHTML=`<div style="display:flex;flex-direction:column;gap:10px;">${d.insights.map((t,i)=>insight(t,i)).join('')}</div>`;

      const badge=document.getElementById('an-ai-badge');
      if(badge) badge.style.display=d.ai_generated?'inline-flex':'none';

      // Load coach banner
      if(coachRes){
        try{
          const cd=await coachRes.json();
          if(cd.success) coachBanner(cd.coach);
        }catch{}
      }

      if(typeof window.loadGamificationStats==='function') window.loadGamificationStats();

      // Pulse the last-updated timestamp
      const tsEl=document.getElementById('an-last-updated');
      if(tsEl) tsEl.textContent='Updated '+new Date().toLocaleTimeString();
    }catch(e){
      console.error('Analytics load error:',e);
      document.querySelectorAll('.an-stat-val').forEach(el=>el.style.opacity='1');
    }
  };

  // Auto-refresh every 60s when analytics tab is visible
  let _autoRefresh=null;
  function startAutoRefresh(){ _autoRefresh=setInterval(()=>{ if(document.getElementById('tab-analytics')?.classList.contains('active-tab-content')) window.loadAnalytics(); },60000); }
  function stopAutoRefresh(){ if(_autoRefresh){clearInterval(_autoRefresh);_autoRefresh=null;} }

  document.addEventListener('click',async(e)=>{
    if(e.target.closest('#btn-analytics-refresh')) window.loadAnalytics();
    if(e.target.closest('#btn-analytics-csv')){
      try{
        const res=await fetch('/api/analytics/data');
        const d=await res.json();
        if(!d.success) return;
        const s=d.stats;
        const rows=[['Metric','Value'],['Total',s.total],['Completed',s.completed],['Pending',s.pending],['Overdue',s.overdue],['Completion Rate',s.completion_rate+'%'],['Productivity Score',s.productivity_score],['Score Label',s.score_label],['Streak',s.streak+' days'],...(d.insights||[]).map((t,i)=>['Insight '+(i+1),t])];
        const csv=rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\n');
        const a=document.createElement('a');
        a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
        a.download='mint-analytics-'+new Date().toISOString().slice(0,10)+'.csv';
        a.click();
      }catch{}
    }
    const tab=e.target.closest('.nav-tab');
    if(tab&&tab.dataset.tab==='tab-analytics'){
      setTimeout(window.loadAnalytics,150);
      startAutoRefresh();
    } else if(tab&&tab.dataset.tab!=='tab-analytics'){
      stopAutoRefresh();
    }
  });
})();
