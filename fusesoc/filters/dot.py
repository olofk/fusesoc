import os


class Dot:
    def run(self, edam, work_root):
        nodes = []
        edges = []
        deps = edam.get("dependencies", {})
        for k, v in deps.items():
            nodes.append(k)
            for e in v:
                edges.append((k, e))

        s = "digraph G {\n"
        s += 'rankdir="LR"\n'
        for n in nodes:
            s += f'"{n}";\n'
        for e in edges:
            s += f'"{e[0]}" -> "{e[1]}";\n'
        s += "}\n"
        print(edam["name"])
        with open(os.path.join(work_root, edam["name"] + ".gv"), "w") as f:
            f.write(s)
        return edam
