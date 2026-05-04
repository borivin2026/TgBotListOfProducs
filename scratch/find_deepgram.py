import deepgram
import inspect

def find_member(obj, target, path="deepgram", visited=None):
    if visited is None:
        visited = set()
    
    obj_id = id(obj)
    if obj_id in visited:
        return
    visited.add(obj_id)
    
    try:
        members = dir(obj)
    except:
        return

    for name in members:
        if target.lower() in name.lower():
            print(f"FOUND: {path}.{name}")
        
        try:
            member = getattr(obj, name)
            if inspect.ismodule(member) or inspect.isclass(member):
                if member.__name__.startswith("deepgram"):
                    find_member(member, target, f"{path}.{name}", visited)
        except:
            continue

print("Searching for PrerecordedOptions...")
find_member(deepgram, "PrerecordedOptions")
print("Searching for FileSource...")
find_member(deepgram, "FileSource")
print("Searching for Options...")
find_member(deepgram, "Options")
