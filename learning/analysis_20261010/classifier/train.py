"""Multinomial logistic regression on the view features; held-out by game. Reports accuracy after 10/20/40 plies,
overall and from our own side, plus how well it singles out the classes that drive decisions."""
import os, numpy as np, torch
torch.set_num_threads(1)
d = np.load(os.path.join(os.path.dirname(__file__), "dataset.npz"))
y = d["y"]; persp = d["persp"]; gid = d["gid"]; classes = list(d["classes"])
ug = np.unique(gid); rng = np.random.default_rng(1); test_g = set(rng.choice(ug, size=len(ug) // 5, replace=False))
te = np.array([g in test_g for g in gid]); tr = ~te
ours = persp == "IAmAVirus"
for N in (10, 20, 40):
    X = d[f"X{N}"]; mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-4
    Xt = torch.tensor((X - mu) / sd); yt = torch.tensor(y)
    W = torch.zeros(X.shape[1], len(classes), requires_grad=True); b = torch.zeros(len(classes), requires_grad=True)
    opt = torch.optim.LBFGS([W, b], max_iter=300, line_search_fn="strong_wolfe")
    idx = torch.tensor(np.nonzero(tr)[0])
    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.cross_entropy(Xt[idx] @ W + b, yt[idx]) + 1e-3 * (W ** 2).sum()
        loss.backward(); return loss
    opt.step(closure)
    with torch.no_grad():
        P = torch.softmax(Xt @ W + b, 1).numpy()
    pred = P.argmax(1)
    acc = (pred[te] == y[te]).mean(); acc_ours = (pred[te & ours] == y[te & ours]).mean() if (te & ours).any() else float("nan")
    # decision groups
    tapa = np.isin(y, [classes.index("TA Baseline P"), classes.index("TA Baseline A")])
    p_tapa = P[:, classes.index("TA Baseline P")] + P[:, classes.index("TA Baseline A")]
    def auc(score, pos):
        s = score[te]; t = pos[te]; o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(len(s))
        npos = t.sum(); nneg = len(t) - npos
        return (r[t].sum() - npos * (npos - 1) / 2) / max(1, npos * nneg)
    mist = y == classes.index("Mist Opportunities"); p_mist = P[:, classes.index("Mist Opportunities")]
    top = np.isin(y, [classes.index(c) for c in ["Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"]])
    p_top = sum(P[:, classes.index(c)] for c in ["Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"])
    print(f"after {N:>2} plies: 12-way accuracy {acc:.1%} (held-out games), from our side {acc_ours:.1%} (n={int((te & ours).sum())}); "
          f"AUC TA-P/A vs rest {auc(p_tapa, tapa):.3f}, top six vs rest {auc(p_top, top):.3f}, Mist vs rest {auc(p_mist, mist):.3f}")
    if N == 20:
        np.savez(os.path.join(os.path.dirname(__file__), "model20.npz"), W=W.detach().numpy(), b=b.detach().numpy(), mu=mu, sd=sd, classes=np.array(classes))
print("chance (majority class):", f"{np.bincount(y[te]).max() / te.sum():.1%}")
