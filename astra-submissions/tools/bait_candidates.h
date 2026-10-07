// Experimental candidate admission, not a probability that an opponent takes bait.
#ifndef ASTRA_BAIT_CANDIDATES_H_
#define ASTRA_BAIT_CANDIDATES_H_

#include <algorithm>
#include <vector>

#include "tactical_labels.h"

namespace fow::astra {

struct BaitCandidate {
  Move move = kNullMove;
  double hidden_king_bait_fraction = 0.0;
  double mean_conditional_material_cp = 0.0;
  int particles_checked = 0;
};

// Each particle contributes its BEST concealed recapture opportunity, not a
// sum of mutually exclusive replies. A king capture loses immediately; a
// material recapture must leave our king safe. This is a setup/coverage score:
// the opponent may ignore the bait, or infer its defender from their history.
inline BaitCandidate DescribeBait(const std::vector<Position>& particles,
                                 int our_side, int en_passant, Move move,
                                 int maximum_particles) {
  BaitCandidate result;
  result.move = move;
  if (particles.empty() || maximum_particles <= 0) return result;
  const std::size_t count = std::min<std::size_t>(particles.size(), maximum_particles);
  int king_bait_worlds = 0;
  long long material_sum = 0;
  for (std::size_t sample = 0; sample < count; ++sample) {
    // Deterministic, evenly spaced population coverage; does not advance the
    // engine's search RNG. Diagnostic quantity, not rare-event safety coverage.
    Position after = particles[(sample * particles.size()) / count];
    after.set_side_to_move(our_side);
    after.set_en_passant_square(en_passant);
    MoveList available;
    after.GenerateMoves(&available);
    bool legal = false;
    for (Move candidate : available) legal |= candidate == move;
    ++result.particles_checked;
    if (!legal) continue;  // Inconsistent particles contribute zero, never upside.
    UndoState undo;
    after.MakeMove(move, &undo);
    if (after.PreviousMoverIsLost()) continue;
    bool has_king_bait = false;
    int material_best = 0;
    for (const CaptureOpportunity& opportunity : CaptureOpportunities(after)) {
      has_king_bait |= opportunity.fatal_king_bait;
      if (ProfitableHiddenRecapture(opportunity)) {
        material_best = std::max(material_best, opportunity.best_hidden_recapture_net_cp);
      }
    }
    king_bait_worlds += has_king_bait;
    material_sum += material_best;
  }
  result.hidden_king_bait_fraction = static_cast<double>(king_bait_worlds) / count;
  result.mean_conditional_material_cp = static_cast<double>(material_sum) / count;
  return result;
}

inline bool HasBait(const BaitCandidate& candidate) {
  return candidate.hidden_king_bait_fraction > 0.0 || candidate.mean_conditional_material_cp > 0.0;
}

inline bool BaitBefore(const BaitCandidate& a, const BaitCandidate& b) {
  if (a.hidden_king_bait_fraction != b.hidden_king_bait_fraction)
    return a.hidden_king_bait_fraction > b.hidden_king_bait_fraction;
  if (a.mean_conditional_material_cp != b.mean_conditional_material_cp)
    return a.mean_conditional_material_cp > b.mean_conditional_material_cp;
  return a.move < b.move;
}

}  // namespace fow::astra
#endif
