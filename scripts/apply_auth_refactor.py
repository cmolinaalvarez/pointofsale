import os, re, sys, io, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROUTERS = ROOT / "backend" / "app" / "routers"

def ensure_imports(txt: str) -> str:
    if "from fastapi import" in txt:
        txt = re.sub(
            r"(from\s+fastapi\s+import\s+)([^\n]+)",
            lambda m: m.group(1) + ", ".join(sorted(set([x.strip() for x in (m.group(2)+", Depends, Request").split(",") if x.strip()]))),
            txt, count=1
        )
    else:
        # inserta import de fastapi después del primer bloque de imports
        lines = txt.splitlines()
        insert_idx = 0
        for i,l in enumerate(lines[:30]):
            if l.startswith("from ") or l.startswith("import "):
                insert_idx = i+1
        lines.insert(insert_idx, "from fastapi import Depends, Request")
        txt = "\n".join(lines)

    if "backend.app.dependencies.auth" not in txt:
        lines = txt.splitlines()
        insert_idx = 0
        for i,l in enumerate(lines[:80]):
            if l.startswith("from backend.app") or l.startswith("from app.") or l.startswith("import backend.app"):
                insert_idx = i+1
        lines.insert(insert_idx, "from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id")
        txt = "\n".join(lines)

    # elimina import legado si existe
    txt = re.sub(r'from\s+app\.dependencies\.current_user\s+import\s+.*\n', '', txt)
    return txt

def add_router_dependency(txt: str) -> str:
    # agrega dependencies=[Depends(get_current_user)] al APIRouter si falta
    def repl(m):
        inside = m.group(1)
        if "dependencies=" in inside and "get_current_user" in inside:
            return m.group(0)
        if "dependencies=" in inside:
            inside2 = re.sub(r"dependencies\s*=\s*\[([^\]]*)\]",
                             lambda mm: f"dependencies=[{mm.group(1).strip()}, Depends(get_current_user)]",
                             inside)
            if inside2 == inside:
                inside2 = inside.rstrip() + ", dependencies=[Depends(get_current_user)]"
        else:
            sep = ", " if inside.strip() else ""
            inside2 = inside + f"{sep}dependencies=[Depends(get_current_user)]"
        return f"router = APIRouter({inside2})"
    return re.sub(r"router\s*=\s*APIRouter\((.*?)\)", repl, txt, flags=re.S)

def stage2_signature_cleanup(txt: str) -> str:
    # current_user: User = Depends(get_current_user) -> uid: str = Depends(current_user_id)
    txt = re.sub(
        r'\bcurrent_user\s*:\s*User\s*=\s*Depends\(\s*get_current_user\s*\)',
        'uid: str = Depends(current_user_id)',
        txt
    )
    # current_user.id -> uid
    txt = re.sub(r'\bcurrent_user\s*\.\s*id\b', 'uid', txt)
    return txt

def process_file(p: pathlib.Path) -> bool:
    src = p.read_text(encoding="utf-8", errors="ignore")
    orig = src
    src = ensure_imports(src)
    src = add_router_dependency(src)
    src = stage2_signature_cleanup(src)
    if src != orig:
        p.write_text(src, encoding="utf-8")
        return True
    return False

def main():
    changed = 0
    for f in ROUTERS.glob("*.py"):
        if f.name in ("auth.py","deps.py"):
            continue
        if process_file(f):
            changed += 1
    print(f"Routers modificados: {changed}")

if __name__ == "__main__":
    main()
