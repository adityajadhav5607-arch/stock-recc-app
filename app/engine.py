# engine.py
from typing import List, Dict
from universe import GOALS

def dedupe_keep_order(items: List[Dict]) -> List[Dict]:
    seen=set(); out=[]
    for it in items:
        if it["symbol"] in seen: continue
        seen.add(it["symbol"]); out.append(it)
    return out

def apply_excludes(items: List[Dict], exclude: List[str]) -> List[Dict]:
    excl={e.lower() for e in (exclude or [])}; out=[]
    for it in items:
        tags={t.lower() for t in it.get("tags",[])}
        if it["symbol"].lower() in excl or tags.intersection(excl): continue
        out.append(it)
    return out

def bias_includes(items: List[Dict], include: List[str]) -> List[Dict]:
    inc={i.lower() for i in (include or [])}
    scored=[]
    for it in items:
        s=0; tags={t.lower() for t in it.get("tags",[])}
        if tags.intersection(inc): s+=2
        if it["symbol"].lower() in inc: s+=3
        scored.append((s,it))
    scored.sort(key=lambda x:x[0], reverse=True)
    return [it for _,it in scored]

def apply_risk(items: List[Dict], risk: str) -> List[Dict]:
    if risk=="low":
        scored=[(1 if it["type"]=="ETF" else 0, it) for it in items]
        scored.sort(key=lambda x:x[0], reverse=True)
        return [it for _,it in scored]
    return items

def recommend(goal: str, risk: str, include: List[str], exclude: List[str], k: int):
    if goal not in GOALS: return [], "Unknown goal."
    base=dedupe_keep_order(GOALS[goal]["core"][:])
    base=apply_excludes(base, exclude)
    base=bias_includes(base, include)
    base=apply_risk(base, risk)
    out=[]
    for it in base[:k]:
        why=["matches "+goal.replace("_"," ")]
        if risk=="low" and it["type"]=="ETF": why.append("ETF favored for low risk")
        if it.get("tags"): why.append("tags: "+", ".join(it["tags"][:2]))
        out.append({"symbol":it["symbol"],"name":it["name"],"type":it["type"],"why":"; ".join(why)})
    return out, GOALS[goal].get("note","")
