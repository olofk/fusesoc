import os


class Coredepsmk:
    def run(self, edam, work_root):
        nodes = []
        edges = []
        deps = edam.get("dependencies", {})
        for k, v in deps.items():
            nodes.append(k)
            for e in v:
                edges.append((k, e))

        s = "fusesoc-deps := \\\n  "
        filenames = [f["name"] for f in edam["files"]]
        filenames += [c["core_file"] for c in edam["cores"].values()]
        s += " \\\n  ".join(
            [os.path.abspath(os.path.join(work_root, f)) for f in filenames]
        )

        with open(os.path.join(work_root, "core-deps.mk"), "w") as f:
            f.write(s)
        return edam
