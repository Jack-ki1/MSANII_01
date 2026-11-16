export const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
.m{--b:#087fe5;--sk:#27b9f5;--bd:#0756b5;--lm:#d8fa20;--ink:#111820;--mu:#687586;--m2:#8d98a6;--ln:#e6ebf1;--sf:#f7f9fc;--sb:#f0f7ff;--sl:#f6ffd6;--gn:#1f9d73;--am:#e39a21;--rd:#dc5555;font:500 14px/1.55 "Plus Jakarta Sans",ui-sans-serif,system-ui,sans-serif;color:var(--ink);background:var(--sf);min-height:100vh;font-variant-numeric:tabular-nums}
.m *{box-sizing:border-box}.m h1,.m h2,.m h3,.m p{margin:0}.m p+p{margin-top:8px}
.m h1,.m h2,.m h3,.lg{font-family:"Bricolage Grotesque","Plus Jakarta Sans",system-ui,sans-serif;letter-spacing:-.025em;font-weight:800}
.m button,.m input,.m select,.m textarea{font:inherit;color:inherit}.m :focus-visible{outline:2px solid var(--b);outline-offset:2px}
.btn{border:0;border-radius:10px;padding:9px 18px;font-weight:700;cursor:pointer;background:var(--b);color:#fff;transition:background .15s}.btn:hover{background:var(--bd)}
.btn.lm{background:var(--lm);color:var(--ink);border-radius:99px}.btn.lm:hover{background:#c6e80e}
.btn.gh{background:transparent;color:#fff;border:1.5px solid rgba(255,255,255,.75);border-radius:99px}.btn.gh:hover{background:rgba(255,255,255,.16)}
.btn.g{background:#fff;color:var(--ink);border:1px solid var(--ln)}.btn.g:hover{background:var(--sb)}.btn:disabled{opacity:.45;cursor:not-allowed}
.inp{background:#fff;border:1px solid var(--ln);border-radius:10px;padding:8px 11px;width:100%}.inp:focus{border-color:var(--b)}
.pn{background:#fff;border:1px solid var(--ln);border-radius:18px;padding:18px;box-shadow:0 8px 28px rgba(14,70,126,.06);margin-bottom:14px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.sp{justify-content:space-between}.mu{color:var(--mu)}.sm{font-size:12px}
.tag{display:inline-block;padding:2px 10px;border-radius:99px;font-size:12px;font-weight:700;background:var(--sf);color:var(--mu);border:1px solid var(--ln)}
.tag.bl{background:var(--sb);color:var(--b);border-color:#cfe6ff}.tag.gn{background:var(--sl);color:var(--gn);border-color:#e1f59a}.tag.am{background:#fff4de;color:#b3741a;border-color:#fbe1b0}.tag.rd{background:#fdecec;color:var(--rd);border-color:#f8cfcf}
.seg{display:inline-flex;background:var(--sf);border:1px solid var(--ln);border-radius:10px;padding:3px}.seg button{border:0;background:none;padding:5px 12px;border-radius:8px;cursor:pointer;font-weight:600;color:var(--mu)}.seg button.on{background:var(--b);color:#fff}.seg button:disabled{opacity:.4;cursor:not-allowed}
.lg{display:inline-flex;align-items:center;gap:8px;font-size:22px}
.shell{display:grid;grid-template-columns:236px 1fr;min-height:100vh}
.side{background:#fff;border-right:1px solid var(--ln);padding:20px 14px;display:flex;flex-direction:column;gap:4px;position:sticky;top:0;height:100vh}
.nv{display:flex;gap:10px;align-items:center;width:100%;text-align:left;background:none;border:0;padding:10px 12px;border-radius:12px;color:var(--mu);font-weight:700;cursor:pointer}.nv:hover{background:var(--sf);color:var(--ink)}.nv.on{background:var(--sb);color:var(--b)}.nv:disabled{opacity:.4;cursor:not-allowed}
.main{padding:24px 28px;min-width:0}.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px}.top h2{font-size:28px}
.bn{background:#fff4de;color:#9a6212;border-radius:10px;padding:6px 12px;font-size:12px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.card{background:#fff;border:1px solid var(--ln);border-radius:18px;padding:16px;cursor:pointer;text-align:left;box-shadow:0 8px 28px rgba(14,70,126,.06);transition:transform .15s,border-color .15s}.card:hover{transform:translateY(-2px);border-color:var(--sk)}
.av{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;font-weight:800;color:#fff;flex:none}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}.kp{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:14px 0}
.kpi{background:#fff;border:1px solid var(--ln);border-radius:14px;padding:12px}.kpi h3{font-size:26px;margin:2px 0}.sp2{width:100%;height:32px;display:block}
.an{display:grid;grid-template-columns:180px 1fr;gap:18px}.sub{display:flex;flex-direction:column;gap:2px}.sub button{text-align:left;background:none;border:0;padding:8px 12px;border-radius:10px;color:var(--mu);font-weight:600;cursor:pointer}.sub button.on{background:var(--sb);color:var(--b)}
.mtr{height:8px;background:var(--ln);border-radius:4px;overflow:hidden}.mtr i{display:block;height:100%;background:linear-gradient(90deg,var(--sk),var(--lm))}
.ch{width:100%;height:170px;display:block}.bars{display:flex;gap:12px;height:190px}.bc{flex:1;text-align:center;font-size:11px;color:var(--mu);display:flex;flex-direction:column;gap:6px}
.bt{flex:1;display:flex;align-items:flex-end;background:var(--sf);border-radius:10px;overflow:hidden}.bt i{display:block;width:100%;background:linear-gradient(var(--sk),var(--b));color:#fff;font-style:normal;font-weight:700;padding-top:4px;font-size:12px}.bt u{margin:auto;text-decoration:none;color:var(--m2)}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:9px 8px;border-bottom:1px solid var(--ln);vertical-align:top}th{color:var(--mu);font-size:12px;font-weight:700}
.hero{position:relative;overflow:hidden;color:#fff;background:radial-gradient(ellipse at 76% 45%,rgba(179,241,255,.45),transparent 38%),linear-gradient(112deg,#0873d2 0%,#078fe9 52%,#25baf5 100%);padding:22px 48px 150px}
.hn{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:48px}.hl{display:flex;gap:28px;font-weight:600}.hl span{opacity:.92}
.hb{display:grid;grid-template-columns:1.05fr 1fr;gap:24px;align-items:center;position:relative;z-index:1}.hh{font-size:56px;line-height:1.02;margin-bottom:16px}.hh em{font-style:normal;color:var(--lm)}.hb p.lead{max-width:440px;font-size:16px;opacity:.95;margin-bottom:22px}
.fl{display:flex;gap:14px;align-items:center;justify-content:center}.fc{background:#fff;color:var(--ink);border-radius:18px;padding:14px;width:170px;box-shadow:0 24px 50px rgba(0,40,100,.28)}.fc h2{font-size:30px}
.cl{position:absolute;left:0;right:0;bottom:-1px;height:130px;background:radial-gradient(ellipse at 6% 100%,#fff 0 22%,transparent 23%),radial-gradient(ellipse at 24% 108%,#fff 0 20%,transparent 21%),radial-gradient(ellipse at 45% 112%,#fff 0 22%,transparent 23%),radial-gradient(ellipse at 67% 106%,#fff 0 21%,transparent 22%),radial-gradient(ellipse at 90% 100%,#fff 0 23%,transparent 24%)}
.feat{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:18px;padding:12px 48px 30px}.feat div{display:flex;gap:12px}.ic{width:38px;height:38px;border-radius:50%;background:var(--sb);color:var(--b);display:grid;place-items:center;flex:none;font-size:16px}
.sec{text-align:center;padding:24px 24px 10px}.sec h2{font-size:38px;line-height:1.1}.sec h2 b{color:var(--b)}.sec h2 em{font-style:normal;background:var(--lm);padding:0 8px;border-radius:8px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;padding:18px 48px}.stats .pn{margin:0}.stats h2{font-size:44px;color:var(--b)}
.lime{background:var(--lm);border-color:var(--lm)}.lime h2{color:var(--ink);font-size:22px}
.band{margin:10px 48px 40px;background:var(--sb);border-radius:20px;padding:22px 28px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.lw{display:grid;grid-template-columns:1fr 1fr;min-height:100vh}.lp{background:linear-gradient(112deg,#0873d2,#27b9f5);color:#fff;padding:48px;display:flex;flex-direction:column;justify-content:space-between}.lp h1{font-size:44px;line-height:1.05}.lp h1 em{font-style:normal;color:var(--lm)}.lf{display:grid;place-items:center;padding:24px;background:#fff}
@media(max-width:860px){.shell,.lw,.an,.two,.hb{grid-template-columns:1fr}.side{position:static;height:auto}.hh{font-size:38px}.fl,.hl{display:none}.hero,.feat,.stats{padding-left:20px;padding-right:20px}.band{margin:10px 20px 30px}.main{padding:16px}.lp{padding:28px}}
`;
