"""Standalone presentation figure from the preserved native trace."""
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"astra-submissions/analysis/decision-tradeoff-20261111"


def main():
    result=json.loads((OUT/"result.json").read_text())
    case=next(c for c in result["cases"] if c["role"]=="loss")
    rows=case["per_world"];colors=["#b16a48" if r["actual"] else "#3e3e3e" if r["contribution"]>0 else "#c7c7c7" for r in rows]
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none","axes.unicode_minus":True})
    fig=plt.figure(figsize=(12,8),facecolor="white")
    ax=fig.add_axes([.1,.14,.58,.72]);side=fig.add_axes([.74,.14,.24,.72]);side.axis("off")
    fig.text(.06,.95,"A close average hides large disagreements",fontsize=19,fontweight="bold",color="#292929")
    fig.text(.06,.91,"v38 saved search · ewav2dzr · before Qxd5 · all 22 worlds searched",fontsize=11,color="#777777")
    ax.barh(range(len(rows)),[r["contribution"] for r in rows],color=colors,height=.65)
    ax.set_yticks(range(len(rows)),[str(r["index"]) for r in rows])
    for label,row in zip(ax.get_yticklabels(),rows):
        if row["actual"]:label.set_color("#a25c3c");label.set_fontweight("bold")
    ax.invert_yaxis();ax.axvline(0,color="#999999",linewidth=.8)
    for i,row in enumerate(rows):
        if row["actual"]:ax.text(-.0045,i,"actual board",ha="right",va="center",fontsize=9,color="#a25c3c")
    ax.set_xlim(-.065,.061);ax.xaxis.set_major_locator(ticker.MultipleLocator(.02))
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%+.02f"))
    ax.grid(axis="x",color="#eeeeee",linewidth=.8);ax.set_axisbelow(True)
    ax.set_title("World probability × (Qxd5 value − h4 value)",loc="left",fontsize=11,pad=12,color="#4e4e4e")
    ax.set_xlabel("← favours h4                  contribution to utility                  favours Qxd5 →",labelpad=12,color="#666666",fontsize=9)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.tick_params(axis="both",length=0,labelcolor="#666666",pad=5)
    side.text(0,.98,"NET ADVANTAGE",fontsize=10,color="#777777",va="top")
    side.text(0,.92,f"+{case['gap']:.6f}",fontsize=27,fontweight="bold",color="#303030",va="top")
    side.text(0,.83,"Qxd5 is preferred in this tree.",fontsize=10,color="#555555",va="top")
    side.text(0,.71,f"Qxd5   {case['chosen_value']:.6f}\nh4         {case['alternate_value']:.6f}",fontsize=12,color="#444444",linespacing=1.7,va="top")
    actual=case["actual_world"]
    side.text(0,.54,"THE ACTUAL BOARD",fontsize=10,color="#a25c3c",va="top")
    side.text(0,.48,f"Model weight    {100*actual['weight']:.2f}%\nContribution    {actual['contribution']:+.6f}",fontsize=11,color="#555555",linespacing=1.7,va="top")
    side.text(0,.31,"In the actual board, these\nestimates favour h4.\nOther worlds outweigh it.",fontsize=11,color="#555555",linespacing=1.6,va="top")
    side.text(0,.14,"Utilities are model estimates,\nnot win probabilities.\nSaved continuations held fixed.",fontsize=9,color="#777777",linespacing=1.7,va="top")
    fig.text(.06,.035,"Post-hoc diagnosis from one frozen replay. This chart does not establish an evaluation error, convergence or strength gain.",fontsize=9,color="#777777")
    png=OUT/"decision-tradeoff.png";svg=OUT/"decision-tradeoff.svg"
    assert not png.exists() and not svg.exists()
    fig.savefig(png,dpi=180,facecolor="white")
    fig.savefig(svg,facecolor="white",metadata={"Date":None})
    plt.close(fig)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
    ET.parse(svg)
    receipt=dict(python=sys.version,matplotlib=matplotlib.__version__,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256=hashlib.sha256((OUT/"result.json").read_bytes()).hexdigest(),
        figures={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [png,svg]},svg_xml_parses=True)
    with (OUT/"figure.json").open("x") as f:json.dump(receipt,f,indent=1,sort_keys=True);f.write("\n")
    print(json.dumps(dict(figures=list(receipt["figures"]),svg_xml_parses=True)))


if __name__=="__main__":main()
