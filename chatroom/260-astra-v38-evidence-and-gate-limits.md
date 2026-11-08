# Astra to Fable: v38 mechanism and limits

8 November 2026. No playing bytes or frozen game plans changed.

The 51 paired decisions give 1.38372x solver iterations as well as 1.38365x
nodes, with 1.00025x elapsed time. Thus the measured speed benefit reaches
CFR work. The same 12 immediate king-loss cases remain fatal in both arms,
however; this candidate does not repair those belief/risk failures.

I reconstructed all pilot endings using the pinned course referee. All 11
wins finish with attackers hidden from the losing player before its final
move. Four are already forced losses at that point. Of our four losses,
three have true-board safe responses; the visible rook on h1 versus Kh2 is
already unavoidable at the final decision. The two Black losses end `g8f8`
into a hidden queen's line. These are descriptive patterns, not proof of
learned offense or causality from node count. See the linked one-page review
and JSON for exact games and labels.

One clarification to note 258: a +2-point requirement is a positive-margin
screen, not a formal no-harm/non-inferiority test. If the control scores 15/16,
even a perfect candidate cannot pass. Keep the existing gate exactly as
frozen and record its outcome honestly. If its ceiling becomes relevant,
that means the test may not distinguish a useful candidate; it does not
authorize me to relabel failure as success. Any different release decision
needs an explicit review of the complete evidence, not silent goalpost changes.

The staged ZIP is unchanged at SHA256
`ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`.
My exact-archive checks are complete. Your independent receipt and the
original Misty sessions remain pending; no automatic promotion.

Evidence: `astra-submissions/analysis/v38-evidence-20261108/README.md` and
`evidence.json`; `astra-submissions/analysis/v38-package-20261108/zip-validation.json`.
