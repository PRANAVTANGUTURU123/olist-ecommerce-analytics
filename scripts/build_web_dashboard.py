"""Generates dashboard/olist_web_dashboard.html: a standalone, self-contained
web dashboard (Chart.js) built from dashboard/dashboard_data.json. This is
the "web dashboard" alternative to the Power BI build."""
import json
import re

with open("dashboard/dashboard_data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

DATA_JSON = json.dumps(DATA, separators=(",", ":"))

HTML = r"""<title>Olist Analytics Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.5.1/chart.umd.min.js"></script>
<style>
:root{
  color-scheme: light;
  --page-bg:#f9f9f7; --surface:#fcfcfb; --surface-2:#f2f1ec; --sidebar-bg:#f3f2ee;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#898781;
  --grid:#e1e0d9; --baseline:#c3c2b7; --border:rgba(11,11,11,0.10);
  --accent:#2a78d6; --accent-2:#eb6834;
  --seq-100:#cde2fb; --seq-250:#86b6ef; --seq-350:#5598e7; --seq-450:#2a78d6; --seq-550:#1c5cab; --seq-650:#104281;
  --good:#0ca30c; --critical:#d03b3b; --warning:#fab219;
  --shadow: 0 1px 2px rgba(11,11,11,0.06), 0 4px 12px rgba(11,11,11,0.05);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --page-bg:#0d0d0d; --surface:#1a1a19; --surface-2:#222221; --sidebar-bg:#161615;
    --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#898781;
    --grid:#2c2c2a; --baseline:#383835; --border:rgba(255,255,255,0.10);
    --accent:#3987e5; --accent-2:#d95926;
    --seq-100:#184f95; --seq-250:#1c5cab; --seq-350:#256abf; --seq-450:#3987e5; --seq-550:#5598e7; --seq-650:#86b6ef;
    --good:#0ca30c; --critical:#e66767; --warning:#fab219;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 4px 16px rgba(0,0,0,0.35);
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --page-bg:#0d0d0d; --surface:#1a1a19; --surface-2:#222221; --sidebar-bg:#161615;
  --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#898781;
  --grid:#2c2c2a; --baseline:#383835; --border:rgba(255,255,255,0.10);
  --accent:#3987e5; --accent-2:#d95926;
  --seq-100:#184f95; --seq-250:#1c5cab; --seq-350:#256abf; --seq-450:#3987e5; --seq-550:#5598e7; --seq-650:#86b6ef;
  --good:#0ca30c; --critical:#e66767; --warning:#fab219;
  --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 4px 16px rgba(0,0,0,0.35);
}
*{box-sizing:border-box;}
body{margin:0;background:var(--page-bg);color:var(--text-primary);font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;}
.num{font-family:"IBM Plex Mono","IBM Plex Sans",monospace;font-variant-numeric:tabular-nums;}
.app{display:flex;min-height:100vh;}

/* ---- sidebar ---- */
.sidebar{width:236px;flex:0 0 236px;background:var(--sidebar-bg);border-right:1px solid var(--border);
  display:flex;flex-direction:column;padding:20px 12px;gap:2px;position:sticky;top:0;height:100vh;overflow-y:auto;}
.brand{padding:8px 12px 18px;}
.brand-name{font-weight:700;font-size:15px;letter-spacing:.01em;}
.brand-sub{font-size:11.5px;color:var(--text-muted);margin-top:3px;}
.nav-btn{display:flex;align-items:center;gap:10px;width:100%;text-align:left;border:none;background:none;
  padding:10px 12px;border-radius:8px;font-size:13.5px;font-weight:500;color:var(--text-secondary);cursor:pointer;
  font-family:inherit;transition:background .12s;}
.nav-btn:hover{background:var(--surface-2);}
.nav-btn.active{background:var(--accent);color:#fff;}
.nav-btn .ic{font-size:15px;width:18px;text-align:center;}
.sidebar-foot{margin-top:auto;padding:14px 12px 4px;font-size:11px;color:var(--text-muted);border-top:1px solid var(--border);}

/* ---- main ---- */
.main{flex:1;min-width:0;padding:28px 36px 60px;max-width:1240px;}
.page-head{margin-bottom:22px;}
.page-title{font-size:22px;font-weight:700;margin:0 0 4px;}
.page-desc{font-size:13.5px;color:var(--text-secondary);margin:0;max-width:640px;line-height:1.5;}
.section{display:none;}
.section.active{display:block;animation:fade .25s ease;}
@keyframes fade{from{opacity:0;transform:translateY(3px);}to{opacity:1;transform:none;}}

/* ---- grid & cards ---- */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin-bottom:20px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;box-shadow:var(--shadow);}
.stat{padding:16px 18px;}
.stat-label{font-size:11.5px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600;}
.stat-value{font-size:26px;font-weight:700;margin-top:6px;line-height:1.1;}
.stat-value .unit{font-size:14px;font-weight:600;color:var(--text-secondary);margin-left:2px;}
.stat-delta{font-size:12px;margin-top:5px;font-weight:600;}
.stat-delta.good{color:var(--good);} .stat-delta.bad{color:var(--critical);}

.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}
.chart-grid.single{grid-template-columns:1fr;}
@media (max-width:880px){.chart-grid{grid-template-columns:1fr;}}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:12px;box-shadow:var(--shadow);padding:16px 18px 12px;}
.panel-title{font-size:13.5px;font-weight:600;margin:0 0 2px;}
.panel-sub{font-size:11.5px;color:var(--text-muted);margin:0 0 10px;}
.chart-box{position:relative;height:260px;}
.panel.tall .chart-box{height:380px;}
.chart-box canvas{width:100%!important;height:100%!important;}

.callout{background:var(--surface-2);border:1px solid var(--border);border-left:3px solid var(--accent);
  border-radius:8px;padding:12px 14px;font-size:12.5px;color:var(--text-secondary);line-height:1.55;margin:10px 0 16px;}
.callout b{color:var(--text-primary);}
.callout.warn{border-left-color:var(--critical);}

table{width:100%;border-collapse:collapse;font-size:12.5px;}
thead th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:var(--text-muted);
  font-weight:600;padding:7px 10px;border-bottom:1px solid var(--baseline);position:sticky;top:0;background:var(--surface);}
tbody td{padding:7px 10px;border-bottom:1px solid var(--grid);color:var(--text-secondary);}
tbody td:first-child, tbody td.name{color:var(--text-primary);font-weight:500;}
tbody tr:hover{background:var(--surface-2);}
td.n, th.n{text-align:right;font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;}
.table-wrap{overflow-x:auto;max-height:360px;overflow-y:auto;border-radius:8px;}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;}
.pill.crit{background:color-mix(in srgb, var(--critical) 16%, transparent);color:var(--critical);}
.pill.good{background:color-mix(in srgb, var(--good) 16%, transparent);color:var(--good);}

.stackbar{display:flex;height:34px;border-radius:8px;overflow:hidden;border:1px solid var(--border);}
.stackbar .seg{display:flex;align-items:center;justify-content:center;font-size:11.5px;font-weight:600;color:#fff;white-space:nowrap;}
.legend-row{display:flex;gap:16px;margin-top:8px;font-size:12px;color:var(--text-secondary);}
.legend-row .sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px;}

.two-stat{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.mini-hero{text-align:center;padding:22px 10px;}
.mini-hero .v{font-size:34px;font-weight:700;}
.mini-hero .l{font-size:12px;color:var(--text-muted);margin-top:4px;}

::-webkit-scrollbar{width:9px;height:9px;}
::-webkit-scrollbar-thumb{background:var(--baseline);border-radius:6px;}
</style>

<div class="app">
  <nav class="sidebar">
    <div class="brand">
      <div class="brand-name">Olist Analytics</div>
      <div class="brand-sub">Sep 2016 &ndash; Aug 2018 &middot; 98,198 orders</div>
    </div>
    <button class="nav-btn active" data-section="overview"><span class="ic">&#9673;</span>Overview</button>
    <button class="nav-btn" data-section="category"><span class="ic">&#9635;</span>Category performance</button>
    <button class="nav-btn" data-section="delivery"><span class="ic">&#9737;</span>Delivery &amp; logistics</button>
    <button class="nav-btn" data-section="regional"><span class="ic">&#9711;</span>Regional</button>
    <button class="nav-btn" data-section="payments"><span class="ic">&#9670;</span>Payments &amp; sellers</button>
    <button class="nav-btn" data-section="retention"><span class="ic">&#9672;</span>Customer retention</button>
    <div class="sidebar-foot">Olist Brazilian E-Commerce<br>Data analytics portfolio project</div>
  </nav>

  <main class="main">

    <section class="section active" id="overview">
      <div class="page-head">
        <h1 class="page-title">Executive overview</h1>
        <p class="page-desc">Headline revenue, order volume, and satisfaction metrics across the full order history.</p>
      </div>
      <div class="kpi-row" id="kpi-overview"></div>
      <div class="chart-grid">
        <div class="panel"><div class="panel-title">Monthly revenue</div><div class="panel-sub">Canceled &amp; unavailable orders excluded</div><canvas id="chart-rev-trend"></canvas></div>
        <div class="panel"><div class="panel-title">Monthly order volume</div><div class="panel-sub">Same order set as revenue, indexed to count</div><canvas id="chart-orders-trend"></canvas></div>
      </div>
      <div class="callout"><b>Nov 2017 spike (Black Friday):</b> revenue jumped to R$1.17M, +36% over October &mdash; the sharpest single-month move in the dataset. Growth plateaus through 2018 rather than continuing to climb.</div>
      <div class="chart-grid">
        <div class="panel"><div class="panel-title">Revenue by weekday</div><div class="panel-sub">Weekday orders outweigh weekend by ~40%</div><canvas id="chart-weekday"></canvas></div>
        <div class="panel">
          <div class="panel-title">Order status</div><div class="panel-sub">Share of all 98,596 orders placed</div>
          <div class="mini-hero"><div class="v num">97.0%</div><div class="l">delivered successfully</div></div>
          <div class="table-wrap"><table id="tbl-status"></table></div>
        </div>
      </div>
    </section>

    <section class="section" id="category">
      <div class="page-head">
        <h1 class="page-title">Category performance</h1>
        <p class="page-desc">Which product categories drive revenue &mdash; and which combine real volume with weak satisfaction.</p>
      </div>
      <div class="chart-grid single">
        <div class="panel tall"><div class="panel-title">Top 15 categories by product revenue</div><div class="panel-sub">health_beauty, watches_gifts and bed_bath_table lead</div><canvas id="chart-top-cat"></canvas></div>
      </div>
      <div class="chart-grid">
        <div class="panel tall"><div class="panel-title">Revenue vs. satisfaction</div><div class="panel-sub">Bubble size = order count &middot; top 20 categories by revenue</div><canvas id="chart-cat-scatter"></canvas></div>
        <div class="panel">
          <div class="panel-title">Lowest-rated categories</div><div class="panel-sub">Min. 100 orders</div>
          <div class="table-wrap"><table id="tbl-worst-cat"></table></div>
        </div>
      </div>
      <div class="callout warn"><b>office_furniture</b> stands out: 1,272 orders (real volume) but only a 3.49 average review &mdash; worth a root-cause look (damage in transit? sizing mismatch?).</div>
    </section>

    <section class="section" id="delivery">
      <div class="page-head">
        <h1 class="page-title">Delivery &amp; logistics</h1>
        <p class="page-desc">Actual vs. estimated delivery time, where delays concentrate, and the link to review scores.</p>
      </div>
      <div class="kpi-row" id="kpi-delivery"></div>
      <div class="chart-grid single">
        <div class="panel"><div class="panel-title">Review score by delivery outcome</div><div class="panel-sub">The single strongest driver of satisfaction in this dataset</div><canvas id="chart-review-delay"></canvas></div>
      </div>
      <div class="callout warn"><b>An 8+ day late delivery costs 2.6 stars</b> (4.32&#9733; early vs. 1.73&#9733; very late). Olist's delivery estimates run generous &mdash; orders land 11.2 days ahead of the promised date on average &mdash; which cushions most orders but leaves late ones exposed.</div>
      <div class="chart-grid">
        <div class="panel tall"><div class="panel-title">Late-delivery rate by customer state</div><div class="panel-sub">Top 15 of 27 states, min. 30 delivered orders</div><canvas id="chart-late-state"></canvas></div>
        <div class="panel tall"><div class="panel-title">Late-delivery rate by category</div><div class="panel-sub">Top 15, min. 50 delivered orders</div><canvas id="chart-late-cat"></canvas></div>
      </div>
      <div class="panel" style="margin-top:14px">
        <div class="panel-title">Worst sellers by late rate</div><div class="panel-sub">Min. 20 delivered orders</div>
        <div class="table-wrap"><table id="tbl-worst-sellers-late"></table></div>
      </div>
    </section>

    <section class="section" id="regional">
      <div class="page-head">
        <h1 class="page-title">Regional analysis</h1>
        <p class="page-desc">Where customers and sellers are, and how shipping distance affects delivery time.</p>
      </div>
      <div class="chart-grid">
        <div class="panel tall"><div class="panel-title">Customers &amp; revenue by state</div><div class="panel-sub">Top 10 of 27 states by revenue</div><canvas id="chart-cust-state"></canvas></div>
        <div class="panel tall"><div class="panel-title">Sellers by state</div><div class="panel-sub">Top 10 &mdash; supply is far more concentrated than demand</div><canvas id="chart-seller-state"></canvas></div>
      </div>
      <div class="two-stat" style="margin:6px 0 16px">
        <div class="card mini-hero"><div class="v num">7.9 <span style="font-size:16px;color:var(--text-muted)">days</span></div><div class="l">same-state delivery</div></div>
        <div class="card mini-hero"><div class="v num" style="color:var(--critical)">15.0 <span style="font-size:16px;color:var(--text-muted)">days</span></div><div class="l">different-state delivery (+7.1 days)</div></div>
      </div>
      <div class="chart-grid single">
        <div class="panel tall"><div class="panel-title">Slowest average delivery by customer state</div><div class="panel-sub">Bottom 10 of 27 states &mdash; North &amp; Northeast dominate</div><canvas id="chart-shiptime-state"></canvas></div>
      </div>
    </section>

    <section class="section" id="payments">
      <div class="page-head">
        <h1 class="page-title">Payments &amp; sellers</h1>
        <p class="page-desc">How customers pay, and which sellers put revenue at risk.</p>
      </div>
      <div class="chart-grid">
        <div class="panel"><div class="panel-title">Payment value by type</div><div class="panel-sub">Credit card dominates at 78.3%</div><canvas id="chart-payment-type"></canvas></div>
        <div class="panel"><div class="panel-title">Avg. order value by installment count</div><div class="panel-sub">Bigger baskets get financed in more installments</div><canvas id="chart-installments"></canvas></div>
      </div>
      <div class="two-stat" style="margin:16px 0">
        <div class="card mini-hero"><div class="v num" style="color:var(--critical)">7.0%</div><div class="l">of scored seller revenue is at risk (65 of 814 sellers)</div></div>
        <div class="card mini-hero"><div class="v num">R$778k</div><div class="l">revenue from sellers with &lt;3.5&#9733; avg or &gt;20% late rate</div></div>
      </div>
      <div class="chart-grid">
        <div class="panel">
          <div class="panel-title">Worst-scoring sellers</div><div class="panel-sub">Min. 20 orders &middot; the risk list</div>
          <div class="table-wrap"><table id="tbl-worst-sellers"></table></div>
        </div>
        <div class="panel">
          <div class="panel-title">Top sellers by revenue</div><div class="panel-sub">For contrast</div>
          <div class="table-wrap"><table id="tbl-top-sellers"></table></div>
        </div>
      </div>
    </section>

    <section class="section" id="retention">
      <div class="page-head">
        <h1 class="page-title">Customer retention</h1>
        <p class="page-desc">Repeat-purchase behavior using the true person-level key.</p>
      </div>
      <div class="callout"><b>Caveat:</b> this dataset is a fixed Sept 2016&ndash;Aug 2018 snapshot. "One order in-window" doesn't mean "one order ever" &mdash; some customers likely ordered again after the cutoff. Treat this page as directional, not a retention KPI to optimize against.</div>
      <div class="kpi-row" id="kpi-retention"></div>
      <div class="chart-grid">
        <div class="panel"><div class="panel-title">Customers by order count</div><div class="panel-sub">94,990 unique customers, Sept 2016&ndash;Aug 2018</div><canvas id="chart-order-buckets"></canvas></div>
        <div class="panel">
          <div class="panel-title">Revenue share: repeat vs. one-time</div><div class="panel-sub">Repeat customers are rare but spend disproportionately more</div>
          <div style="margin-top:28px">
            <div class="stackbar">
              <div class="seg" id="seg-repeat" style="background:var(--accent)"></div>
              <div class="seg" id="seg-onetime" style="background:var(--baseline);color:var(--text-primary)"></div>
            </div>
            <div class="legend-row">
              <span><span class="sw" style="background:var(--accent)"></span>Repeat &mdash; <b id="lg-repeat-pct"></b> of revenue, 2,888 customers</span>
              <span><span class="sw" style="background:var(--baseline)"></span>One-time &mdash; <b id="lg-onetime-pct"></b> of revenue, 92,095 customers</span>
            </div>
          </div>
        </div>
      </div>
    </section>

  </main>
</div>

<script>
const DATA = __DATA_JSON__;

function root(){return getComputedStyle(document.documentElement);}
function tok(name){return root().getPropertyValue(name).trim();}
function fmtR$(v){return "R$" + Math.round(v).toLocaleString("en-US");}
function fmtR$M(v){return "R$" + (v/1e6).toFixed(2) + "M";}
function fmtN(v){return Math.round(v).toLocaleString("en-US");}

/* ---------- navigation ---------- */
const navBtns = document.querySelectorAll(".nav-btn");
navBtns.forEach(btn=>{
  btn.addEventListener("click", ()=>{
    navBtns.forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll(".section").forEach(s=>s.classList.remove("active"));
    document.getElementById(btn.dataset.section).classList.add("active");
    setTimeout(()=>window.dispatchEvent(new Event("resize")), 30);
  });
});

/* ---------- KPI tiles ---------- */
function statTile(label, value, unit, delta, deltaClass){
  return `<div class="card stat"><div class="stat-label">${label}</div>
    <div class="stat-value num">${value}${unit?`<span class="unit">${unit}</span>`:""}</div>
    ${delta?`<div class="stat-delta ${deltaClass||""}">${delta}</div>`:""}</div>`;
}
document.getElementById("kpi-overview").innerHTML = [
  statTile("Total revenue", fmtR$M(DATA.kpis.total_revenue)),
  statTile("Orders", fmtN(DATA.kpis.total_orders)),
  statTile("Revenue / order", "R$"+DATA.kpis.revenue_per_order.toFixed(2)),
  statTile("Avg. review score", DATA.kpis.avg_review_score.toFixed(2), "/ 5"),
  statTile("Late deliveries", DATA.kpis.pct_late_orders.toFixed(1), "%"),
].join("");

document.getElementById("kpi-delivery").innerHTML = [
  statTile("Avg. actual delivery", DATA.kpis.avg_delivery_days.toFixed(1), "days"),
  statTile("Avg. estimated window", DATA.kpis.avg_estimated_days.toFixed(1), "days"),
  statTile("Delivered late", DATA.kpis.pct_late_orders.toFixed(1), "%", "of all delivered orders"),
  statTile("Days ahead of estimate", DATA.kpis.avg_days_ahead_of_estimate.toFixed(1), "days avg", "cushions most late risk", "good"),
].join("");

document.getElementById("kpi-retention").innerHTML = [
  statTile("Total customers", fmtN(DATA.kpis.total_customers)),
  statTile("Repeat rate", DATA.kpis.pct_repeat_customers.toFixed(1), "%"),
  statTile("Repeat revenue share", "5.7", "%", "vs. 3.0% of customers", "good"),
  statTile("Median re-order gap", fmtN(DATA.days_between_orders.median_days_between_orders), "days"),
].join("");

/* ---------- stacked revenue-share bar ---------- */
/* Label only renders inside a segment when it's wide enough to fit;
   the narrow "repeat" sliver's value goes in the legend instead (see
   dataviz anti-patterns: never let overflow:hidden crop an in-segment label). */
(function(){
  const repeat = DATA.revenue_share_repeat.find(r=>r.customer_type==="repeat");
  const onetime = DATA.revenue_share_repeat.find(r=>r.customer_type==="one-time");
  const MIN_PCT_FOR_LABEL = 12;
  const repeatEl = document.getElementById("seg-repeat");
  const onetimeEl = document.getElementById("seg-onetime");
  repeatEl.style.width = repeat.pct_of_revenue+"%";
  onetimeEl.style.width = onetime.pct_of_revenue+"%";
  repeatEl.textContent = repeat.pct_of_revenue >= MIN_PCT_FOR_LABEL ? repeat.pct_of_revenue.toFixed(1)+"%" : "";
  onetimeEl.textContent = onetime.pct_of_revenue >= MIN_PCT_FOR_LABEL ? onetime.pct_of_revenue.toFixed(1)+"%" : "";
  document.getElementById("lg-repeat-pct").textContent = repeat.pct_of_revenue.toFixed(1)+"%";
  document.getElementById("lg-onetime-pct").textContent = onetime.pct_of_revenue.toFixed(1)+"%";
})();

/* ---------- order-status table ---------- */
(function(){
  const rowsHtml = DATA.order_status_breakdown.filter(d=>d.order_status!=="delivered").map(d=>
    `<tr><td class="name">${d.order_status}</td><td class="n">${fmtN(d.orders)}</td><td class="n">${d.pct_of_orders.toFixed(2)}%</td></tr>`).join("");
  document.getElementById("tbl-status").innerHTML =
    `<thead><tr><th>Status</th><th class="n">Orders</th><th class="n">Share</th></tr></thead><tbody>${rowsHtml}</tbody>`;
})();

/* ---------- generic table builder ---------- */
function buildTable(elId, cols, rowsArr){
  const thead = "<thead><tr>"+cols.map(c=>`<th class="${c.n?'n':''}">${c.label}</th>`).join("")+"</tr></thead>";
  const tbody = "<tbody>"+rowsArr.map(r=>"<tr>"+cols.map(c=>`<td class="${c.n?'n':''} ${c.name?'name':''}">${c.fmt?c.fmt(r[c.key]):r[c.key]}</td>`).join("")+"</tr>").join("")+"</tbody>";
  document.getElementById(elId).innerHTML = thead+tbody;
}
buildTable("tbl-worst-cat",
  [{key:"category_en",label:"Category",name:true},{key:"orders",label:"Orders",n:true,fmt:fmtN},{key:"avg_review_score",label:"Avg score",n:true,fmt:v=>v.toFixed(2)}],
  DATA.worst_review_categories.slice(0,12));
buildTable("tbl-worst-sellers-late",
  [{key:"seller_id",label:"Seller",name:true,fmt:v=>v.slice(0,10)+"&hellip;"},{key:"state",label:"State"},{key:"delivered_orders",label:"Orders",n:true,fmt:fmtN},{key:"pct_late",label:"Late rate",n:true,fmt:v=>`<span class="pill crit">${v.toFixed(1)}%</span>`}],
  DATA.worst_sellers_late);
buildTable("tbl-worst-sellers",
  [{key:"seller_id",label:"Seller",name:true,fmt:v=>v.slice(0,10)+"&hellip;"},{key:"state",label:"State"},{key:"orders",label:"Orders",n:true,fmt:fmtN},{key:"pct_late",label:"Late",n:true,fmt:v=>v.toFixed(1)+"%"},{key:"avg_review_score",label:"Score",n:true,fmt:v=>`<span class="pill crit">${v.toFixed(2)}</span>`}],
  DATA.seller_scorecard.slice(0,12));
buildTable("tbl-top-sellers",
  [{key:"seller_id",label:"Seller",name:true,fmt:v=>v.slice(0,10)+"&hellip;"},{key:"state",label:"State"},{key:"orders",label:"Orders",n:true,fmt:fmtN},{key:"product_revenue",label:"Revenue",n:true,fmt:fmtR$},{key:"avg_review_score",label:"Score",n:true,fmt:v=>`<span class="pill good">${v.toFixed(2)}</span>`}],
  DATA.top_sellers.slice(0,12));

/* ---------- Chart.js setup ---------- */
Chart.defaults.font.family = "'IBM Plex Sans', system-ui, sans-serif";
Chart.defaults.font.size = 11.5;

function chartColors(){
  return {
    text: tok("--text-secondary"), muted: tok("--text-muted"), grid: tok("--grid"),
    baseline: tok("--baseline"), accent: tok("--accent"), accent2: tok("--accent-2"),
    surface: tok("--surface"), critical: tok("--critical"),
    seq: [tok("--seq-100"), tok("--seq-250"), tok("--seq-350"), tok("--seq-450"), tok("--seq-550"), tok("--seq-650")],
  };
}
function baseGrid(c){ return { color: c.grid, drawTicks:false }; }
function baseTicks(c){ return { color: c.muted, font:{size:11} }; }

const charts = [];
function track(c){ charts.push(c); return c; }

function lineChart(id, labels, values, label, color){
  const c = chartColors();
  return track(new Chart(document.getElementById(id), {
    type:"line",
    data:{ labels, datasets:[{ label, data:values, borderColor:color||c.accent, backgroundColor:(color||c.accent)+"22",
      fill:true, tension:.3, pointRadius:0, pointHoverRadius:5, borderWidth:2 }] },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{mode:"index", intersect:false} },
      interaction:{ mode:"index", intersect:false },
      scales:{ x:{ grid:{display:false}, ticks:{...baseTicks(c), maxRotation:60, autoSkip:true} },
               y:{ grid:baseGrid(c), ticks:{...baseTicks(c), callback:v=>fmtCompact(v)}, border:{display:false} } } }
  }));
}
function fmtCompact(v){
  if(Math.abs(v)>=1e6) return "R$"+(v/1e6).toFixed(1)+"M";
  if(Math.abs(v)>=1e3) return (v/1e3).toFixed(0)+"k";
  return v;
}
function hbarChart(id, labels, values, opts={}){
  const c = chartColors();
  const colors = opts.colors || labels.map(()=>c.accent);
  return track(new Chart(document.getElementById(id), {
    type:"bar",
    data:{ labels, datasets:[{ data:values, backgroundColor:colors, borderRadius:4, borderSkipped:false,
      barPercentage:0.7, categoryPercentage:0.8 }] },
    options:{ indexAxis:"y", responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{label:ctx=>opts.tooltipFmt? opts.tooltipFmt(ctx.raw): ctx.raw} } },
      scales:{ x:{ grid:baseGrid(c), ticks:{...baseTicks(c), callback: opts.xFmt||(v=>v)}, border:{display:false} },
               y:{ grid:{display:false}, ticks:baseTicks(c), border:{display:false} } } }
  }));
}
function bubbleChart(id, points){
  const c = chartColors();
  return track(new Chart(document.getElementById(id), {
    type:"bubble",
    data:{ datasets:[{ data:points, backgroundColor:c.accent+"99", borderColor:c.accent, borderWidth:1 }] },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{ label:ctx=>{
        const p = ctx.raw; return `${p.label}: R$${Math.round(p.x).toLocaleString()} revenue, ${p.y.toFixed(2)}★, ${p.orders} orders`; } } } },
      scales:{ x:{ title:{display:true,text:"Product revenue (R$)",color:c.muted,font:{size:11}}, grid:baseGrid(c), ticks:{...baseTicks(c), callback:v=>fmtCompact(v)}, border:{display:false} },
               y:{ title:{display:true,text:"Avg. review score",color:c.muted,font:{size:11}}, grid:baseGrid(c), ticks:baseTicks(c), border:{display:false} } } }
  }));
}

function renderAll(){
  charts.forEach(c=>c.destroy()); charts.length = 0;
  const c = chartColors();

  lineChart("chart-rev-trend", DATA.monthly_revenue_trend.map(d=>d.year_month), DATA.monthly_revenue_trend.map(d=>d.revenue), "Revenue", c.accent);
  lineChart("chart-orders-trend", DATA.monthly_revenue_trend.map(d=>d.year_month), DATA.monthly_revenue_trend.map(d=>d.orders), "Orders", c.accent2);

  hbarChart("chart-weekday", DATA.revenue_by_weekday.map(d=>d.day_name), DATA.revenue_by_weekday.map(d=>d.revenue),
    { xFmt:fmtCompact, tooltipFmt:v=>fmtR$(v) });

  const topCat = DATA.top_categories.slice(0,15).sort((a,b)=>a.product_revenue-b.product_revenue);
  hbarChart("chart-top-cat", topCat.map(d=>d.category_en), topCat.map(d=>d.product_revenue),
    { xFmt:fmtCompact, tooltipFmt:v=>fmtR$(v) });

  bubbleChart("chart-cat-scatter", DATA.top_categories.map(d=>({x:d.product_revenue, y:d.avg_review_score, r:Math.sqrt(d.orders)/6+4, label:d.category_en, orders:d.orders})));

  const delayOrder = ["7+ days early","on time / early","1-3 days late","4-7 days late","8+ days late"];
  const rvd = [...DATA.review_vs_delay].sort((a,b)=>delayOrder.indexOf(a.delay_bucket)-delayOrder.indexOf(b.delay_bucket));
  const seqColors = [c.seq[0],c.seq[1],c.seq[2],c.seq[4],c.seq[5]];
  hbarChart("chart-review-delay", rvd.map(d=>d.delay_bucket+"  ("+fmtN(d.orders)+" orders)"), rvd.map(d=>d.avg_review_score),
    { colors: seqColors, xFmt:v=>v+"★", tooltipFmt:v=>v.toFixed(2)+" ★ avg" });

  const lateState = [...DATA.late_rate_by_state].sort((a,b)=>b.pct_late-a.pct_late).slice(0,15).reverse();
  hbarChart("chart-late-state", lateState.map(d=>d.state), lateState.map(d=>d.pct_late),
    { xFmt:v=>v+"%", tooltipFmt:v=>v.toFixed(1)+"% late" });

  const lateCat = [...DATA.late_rate_by_category].sort((a,b)=>b.pct_late-a.pct_late).slice(0,15).reverse();
  hbarChart("chart-late-cat", lateCat.map(d=>d.category_en), lateCat.map(d=>d.pct_late),
    { xFmt:v=>v+"%", tooltipFmt:v=>v.toFixed(1)+"% late" });

  const custState = [...DATA.customers_by_state].sort((a,b)=>b.revenue-a.revenue).slice(0,10).reverse();
  hbarChart("chart-cust-state", custState.map(d=>d.state), custState.map(d=>d.revenue), { xFmt:fmtCompact, tooltipFmt:v=>fmtR$(v) });

  const sellState = [...DATA.sellers_by_state].sort((a,b)=>b.sellers-a.sellers).slice(0,10).reverse();
  hbarChart("chart-seller-state", sellState.map(d=>d.state), sellState.map(d=>d.sellers), { xFmt:v=>v, tooltipFmt:v=>fmtN(v)+" sellers" });

  const shipState = [...DATA.shipping_time_by_state].sort((a,b)=>b.avg_delivery_days-a.avg_delivery_days).slice(0,10).reverse();
  hbarChart("chart-shiptime-state", shipState.map(d=>d.state), shipState.map(d=>d.avg_delivery_days), { xFmt:v=>v+"d", tooltipFmt:v=>v.toFixed(1)+" days avg" });

  const pay = [...DATA.payment_type_breakdown].filter(d=>d.payment_type!=="not_defined").sort((a,b)=>a.total_paid-b.total_paid);
  hbarChart("chart-payment-type", pay.map(d=>d.payment_type), pay.map(d=>d.pct_of_payment_value), { xFmt:v=>v+"%", tooltipFmt:v=>v.toFixed(1)+"% of payment value" });

  const instOrder = ["1 (upfront)","2-3","4-6","7-12","13+"];
  const inst = [...DATA.installment_bucket].sort((a,b)=>instOrder.indexOf(a.installment_bucket)-instOrder.indexOf(b.installment_bucket));
  hbarChart("chart-installments", inst.map(d=>d.installment_bucket+" installments"), inst.map(d=>d.avg_order_value),
    { colors:[c.seq[0],c.seq[1],c.seq[2],c.seq[4],c.seq[5]], xFmt:fmtCompact, tooltipFmt:v=>fmtR$(v)+" avg order" });

  const buckOrder = ["1 order","2 orders","3-5 orders","6+ orders"];
  const bucks = [...DATA.orders_per_customer].sort((a,b)=>buckOrder.indexOf(a.order_count_bucket)-buckOrder.indexOf(b.order_count_bucket));
  hbarChart("chart-order-buckets", bucks.map(d=>d.order_count_bucket), bucks.map(d=>d.customers),
    { colors:[c.seq[0],c.seq[2],c.seq[4],c.seq[5]], xFmt:fmtCompact, tooltipFmt:v=>fmtN(v)+" customers" });
}
renderAll();
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderAll);
window.addEventListener("resize", ()=>{}, {passive:true});
</script>
"""

HTML = HTML.replace("__DATA_JSON__", DATA_JSON)
HTML = re.sub(r'<canvas id="([^"]+)"></canvas>', r'<div class="chart-box"><canvas id="\1"></canvas></div>', HTML)

with open("dashboard/olist_web_dashboard.html", "w", encoding="utf-8") as f:
    f.write(HTML)

print("wrote dashboard/olist_web_dashboard.html", len(HTML), "bytes")
