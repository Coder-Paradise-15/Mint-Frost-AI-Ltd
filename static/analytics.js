/* Mint Frost AI - Analytics Controller */
(function () {
  'use strict';
  let charts = {};
  const C = { mint:'#37e6b5',cyan:'#00d2ff',red:'#ff3838',orange:'#ff8225',yellow:'#f1c40f',green:'#2ecc71',purple:'#9b59b6',blue:'#3498db' };
  const PIE = [C.mint,C.orange,C.red,C.cyan,C.yellow,C.purple,C.blue];

  function kill(id){ if(charts[id]){charts[id].destroy();delete charts[id];} }

  function bar(id,labels,values,color){
    kill(id);
    const ctx=document.getElementById(id); if(!ctx)return;
    charts[id]=new Chart(ctx,{type:'bar',data:{labels,datasets:[{data:values,backgroundColor:color+'55',borderColor:color,borderWidth:2,borderRadius:6}]},options:{responsive:true,animation:{duration:700},plugins:{legend:{display:false}},scales:{x:{grid:{color:'rgba(255,255,255,0.05)'},ticks:{color:'rgba(255,255,255,0.5)',font:{size:11}}},y:{beginAtZero:true,grid:{color:'rgba(255,255,255,0.05)'},ticks:{color:'rgba(255,255,255,0.5)',font:{size:11},stepSize:1}}}}});
  }

  function donut(id,labels,values){
    kill(id);
    const ctx=document.getElementById(id); if(!ctx)return;
    charts[id]=new Chart(ctx,{type:'doughnut',data:{labels,datasets:[{data:values,backgroundColor:PIE.slice(0,values.length).map(c=>c+'cc'),borderColor:PIE.slice(0,values.length),borderWidth:2}]},options:{responsive:true,cutout:'65%',animation:{duration:700},plugins:{legend:{position:'bottom',labels:{color:'rgba(255,255,255,0.6)',font:{size:10},padding:8,boxWidth:10}}}}});
  }

  function row(label,val,icon){
    return `<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:8px;font-size:13px;"><span style="color:rgba(255,255,255,0.55);"><i class="fas fa-${icon}" style="width:16px;color:var(--mint);margin-right:6px;"></i>${label}</span><span style="font-weight:700;color:#fff;">${val}</span></div>`;
  }

  function insight(text,i){
    const icons=['lightbulb','chart-bar','exclamation-circle','star','rocket'];
    return `<div style="display:flex;align-items:flex-start;gap:12px;padding:12px 16px;background:rgba(55,230,181,0.04);border:1px solid rgba(55,230,181,0.12);border-radius:10px;font-size:13px;line-height:1.5;color:rgba(255,255,255,0.85);"><i class="fas fa-${icons[i%5]}" style="color:var(--mint);margin-top:2px;flex-shrink:0;"></i><span>${text}</span></div>`;
  }

  window.loadAnalytics = async function(){
    try{
      const res=await fetch('/api/analytics/data');
      const d=await res.json();
      if(!d.success) return;
      const s=d.stats;
      const set=(id,v)=>{const el=document.getElementById(id);if(el)el.textContent=v;};
      set('an-total',s.total);
      set('an-completed',s.completed);
      set('an-pending',s.pending);
      set('an-overdue',s.overdue);
      set('an-rate',s.completion_rate+'%');
      set('an-score',s.productivity_score+'/100');
      set('an-score-label',s.score_label+' 🏆');
      set('an-streak',s.streak+' days');
      bar('chart-daily',d.charts.daily.labels,d.charts.daily.values,C.mint);
      bar('chart-weekly',d.charts.weekly.labels,d.charts.weekly.values,C.cyan);
      donut('chart-risk',d.charts.risk.labels,d.charts.risk.values);
      donut('chart-priority',d.charts.priority.labels,d.charts.priority.values);
      donut('chart-category',d.charts.category.labels,d.charts.category.values);
      const t=d.trends;
      const tEl=document.getElementById('an-trends');
      if(tEl) tEl.innerHTML=row('Most Productive',t.most_productive,'sun')+row('Least Productive',t.least_productive,'moon')+row('Avg Overdue Rate',t.avg_overdue_rate+'%','exclamation-triangle');
      const p=d.predictions;
      const pEl=document.getElementById('an-predictions');
      if(pEl) pEl.innerHTML=row("Tomorrow Load",p.tomorrow_load+' tasks','tasks')+row("Tomorrow Risk",p.tomorrow_risk,'fire')+row("Expected Completion",p.expected_completion+'%','check-circle')+row("Planner Success",p.expected_planner_success+'%','magic');
      const iEl=document.getElementById('an-insights');
      if(iEl&&d.insights&&d.insights.length) iEl.innerHTML=d.insights.map((t,i)=>insight(t,i)).join('');
      const badge=document.getElementById('an-ai-badge');
      if(badge) badge.style.display=d.ai_generated?'inline':'none';
      if (typeof window.loadGamificationStats === 'function') {
        window.loadGamificationStats();
      }
    }catch(e){console.error(e);}
  };

  document.addEventListener('click',async(e)=>{
    if(e.target.closest('#btn-analytics-refresh')) window.loadAnalytics();
    if(e.target.closest('#btn-analytics-csv')){
      try{
        const res=await fetch('/api/analytics/data');
        const d=await res.json();
        if(!d.success) return;
        const s=d.stats;
        const rows=[['Metric','Value'],['Total',s.total],['Completed',s.completed],['Pending',s.pending],['Overdue',s.overdue],['Rate',s.completion_rate+'%'],['Score',s.productivity_score],['Label',s.score_label],['Streak',s.streak],...d.insights.map((t,i)=>['Insight '+(i+1),t])];
        const csv=rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\n');
        const a=document.createElement('a');
        a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
        a.download='mint-analytics-'+new Date().toISOString().slice(0,10)+'.csv';
        a.click();
      }catch{}
    }
    const tab=e.target.closest('.nav-tab');
    if(tab&&tab.dataset.tab==='tab-analytics') setTimeout(window.loadAnalytics,150);
  });
})();
