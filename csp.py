
# (It uses the example files at courses.json and profile2a.txt by default.)


import json
import re

def load_courses(path):
    """Load courses.json and return dict cid -> info."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    courses = {}
    for cid, info in raw.items():
        courses[cid] = {
            "cid": info.get("cid", cid),
            "name": info.get("name", ""),
            "minUnits": int(info.get("minUnits", 0)),
            "maxUnits": int(info.get("maxUnits", info.get("minUnits", 0))),
            "prereqs": list(info.get("prereqs", [])),
            "quarters": list(info.get("quarters", []))
        }
    return courses

def load_profile(path):
    """
    Parse a profile file supporting lines like:
      minUnits 3
      maxUnits 9
      register Aut2017
      taken CS229
      request CS229T weight 2 after CS228 in Aut2017,Win2018
    Returns dict with keys: register, minUnits, maxUnits, taken, requests
    Each request is a dict: {options:[...], quarters: [...]/None, weight:int, after:cid_or_None}
    """
    entries = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            entries.append(s)

    profile = {"register": [], "minUnits": 0, "maxUnits": 9999, "taken": [], "requests": []}

    for ln in entries:
        if ln.startswith("minUnits"):
            profile["minUnits"] = int(ln.split()[1])
        elif ln.startswith("maxUnits"):
            profile["maxUnits"] = int(ln.split()[1])
        elif ln.startswith("register"):
            profile["register"].append(ln.split()[1])
        elif ln.startswith("taken"):
            profile["taken"].append(ln.split()[1])
        elif ln.startswith("request"):
            tail = ln[len("request"):].strip()
            # handle " in " clause
            quarters = None
            if " in " in tail:
                left, right = tail.split(" in ", 1)
                tail = left.strip()
                quarters = [x.strip() for x in right.split(",") if x.strip()]
            # tokenise remaining tail
            parts = re.split(r'\s+', tail)
            opts = []
            weight = 1
            after = None
            i = 0
            while i < len(parts):
                p = parts[i]
                if p.lower() == "weight":
                    try:
                        weight = int(parts[i+1]); i += 2; continue
                    except Exception:
                        i += 1; continue
                if p.lower() == "after":
                    try:
                        after = parts[i+1]; i += 2; continue
                    except Exception:
                        i += 1; continue
                if p.lower() == "or":
                    i += 1; continue
                opts.append(p)
                i += 1
            profile["requests"].append({"options": opts, "quarters": quarters, "weight": weight, "after": after})
    return profile

def season_prefix(term):
    return ''.join(ch for ch in term if not ch.isdigit())

def allowed_slots(cid, courses, reg_terms, req_quarters):
    """Return list of indices in reg_terms where cid can be taken."""
    if cid not in courses:
        return []
    offered = set(courses[cid]["quarters"])
    slots = []
    for idx, term in enumerate(reg_terms):
        pref = season_prefix(term)
        if pref in offered:
            if req_quarters is None:
                slots.append(idx)
            else:
                # req_quarters may contain full term or just season
                ok = any(rq == term or rq == pref for rq in req_quarters)
                if ok:
                    slots.append(idx)
    return slots

def solve(courses, profile):
    reg = profile["register"]
    R = len(profile["requests"])
    minU = profile["minUnits"]
    maxU = profile["maxUnits"]
    taken = set(profile["taken"])
    reqs = profile["requests"]

    # precompute slot lists for each course that appears in any request
    slots_for_course = {}
    for req in reqs:
        for c in req["options"]:
            if c not in slots_for_course:
                slots_for_course[c] = allowed_slots(c, courses, reg, req.get("quarters"))

    # state
    assignment = {i: None for i in range(R)}   # request index -> (cid,slot) or None
    units = [0]*len(reg)
    chosen = set()
    best = {"score": (-1, -1), "assign": None, "units": None}

    # heuristic ordering: process requests with fewest possible placements first
    order = list(range(R))
    def count_options(idx):
        cnt = 0
        for c in reqs[idx]["options"]:
            cnt += len(slots_for_course.get(c, []))
        return cnt or 9999
    order.sort(key=count_options)

    def prereq_possible_before(cid, slot_idx, assigned_map, remaining_reqs):
        # if prereq already taken
        if cid in taken:
            return True
        # if assigned earlier in assigned_map
        for a in assigned_map.values():
            if a is not None and a[0] == cid and a[1] < slot_idx:
                return True
        # if appears in remaining requests and has a slot < slot_idx
        for ri in remaining_reqs:
            if cid in reqs[ri]["options"]:
                poss = allowed_slots(cid, courses, reg, reqs[ri].get("quarters"))
                if any(p < slot_idx for p in poss):
                    return True
        return False

    def score_state(assign_map):
        # primary: number of filled requests, secondary: sum of weights
        filled = sum(1 for v in assign_map.values() if v is not None)
        weight_sum = 0
        for ri, v in assign_map.items():
            if v is not None:
                weight_sum += reqs[ri].get("weight", 1)
        return (filled, weight_sum)

    def backtrack(pos):
        # pos is index into order[]
        # quick prune: any units exceed maxU
        if any(u > maxU for u in units):
            return
        if pos >= len(order):
            # full pass: check min units per term
            if all(u >= minU for u in units):
                sc = score_state(assignment)
                if sc > best["score"]:
                    best["score"] = sc
                    best["assign"] = dict(assignment)
                    best["units"] = units.copy()
            return

        rid = order[pos]
        req = reqs[rid]
        remaining = order[pos+1:]

        # try each option
        for cid in req["options"]:
            if cid in chosen or cid in taken or cid not in courses:
                continue
            poss = slots_for_course.get(cid, [])
            for s in poss:
                if units[s] + courses[cid]["minUnits"] > maxU:
                    continue
                # prereqs check
                ok = True
                for p in courses[cid]["prereqs"]:
                    if not prereq_possible_before(p, s, assignment, remaining):
                        ok = False; break
                if not ok:
                    continue
                # 'after' constraint (if present in request)
                if req.get("after"):
                    after_c = req["after"]
                    # if after course is taken -> it's satisfied (treated as slot -inf)
                    aft_slot = None
                    if after_c in taken:
                        aft_slot = -1
                    else:
                        # maybe assigned already
                        for a in assignment.values():
                            if a is not None and a[0] == after_c:
                                aft_slot = a[1]; break
                    if aft_slot is not None and not (aft_slot < s):
                        continue
                    # if aft_slot is None (not assigned yet) we allow it as long as possibility exists later

                # accept assignment
                assignment[rid] = (cid, s)
                chosen.add(cid)
                units[s] += courses[cid]["minUnits"]
                backtrack(pos+1)
                units[s] -= courses[cid]["minUnits"]
                chosen.remove(cid)
                assignment[rid] = None

        # also allow skipping this request (not taking any course for it)
        backtrack(pos+1)

    backtrack(0)

    if best["assign"] is None:
        return None
    # transform result into mapping course -> term
    mapping = {}
    for ri, val in best["assign"].items():
        if val:
            mapping[val[0]] = reg[val[1]]
    return {"mapping": mapping, "units": best["units"]}


courses = load_courses("courses.json")
profile = load_profile("profile2a.txt")
sol = solve(courses, profile)
if not sol:
    print("No feasible schedule found.")
else:
    print("Schedule:")
    for c,t in sol["mapping"].items():
        print(f"  {c} -> {t}")
    print("Units per term:")
    for term, u in zip(profile["register"], sol["units"]):
        print(f"  {term}: {u}")
