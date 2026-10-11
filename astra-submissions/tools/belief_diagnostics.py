"""Offline belief metrics separating occupancy, type and spatial localization."""
import numpy as np


DENOMINATORS={'hidden_empty_nll':'hidden_empty_squares','hidden_occupancy_nll':'hidden_squares',
              'hidden_occupancy_brier':'hidden_squares','hidden_predicted_occupancy':'hidden_squares',
              'hidden_conditional_type_nll':'hidden_enemy_squares','hidden_location_nll':'hidden_enemy_squares'}
DENOMINATORS.update({f'hidden_piece_{k}_location_nll':f'hidden_piece_{k}' for k in range(6)})


def components(belief,mask,truth):
    squares=np.flatnonzero(mask);p=belief[squares].astype(float);y=truth[squares]
    if not len(squares):return {},0
    occupied=y!=6;occ=(1-p[:,6]).clip(1e-12,1-1e-12)
    counts=int((~occupied).sum())
    sums={'hidden_empty_nll':float(-np.log(p[~occupied,6].clip(1e-12,1)).sum()),
          'hidden_occupancy_nll':float(-np.where(occupied,np.log(occ),np.log1p(-occ)).sum()),
          'hidden_occupancy_brier':float(((occ-occupied)**2).sum()),
          'hidden_predicted_occupancy':float(occ.sum()),
          'hidden_conditional_type_nll':float(-np.log((p[occupied,y[occupied]]/occ[occupied]).clip(1e-12,1)).sum()),
          'hidden_location_nll':0.}
    for k in range(6):
        # Distribution over hidden square addresses, conditional on piece type.
        # Count each true piece; multiple identical pieces share this target.
        total=p[:,k].sum();loc=p[y==k,k]/max(total,1e-12)
        nll=float(-np.log(loc.clip(1e-12,1)).sum())
        sums[f'hidden_piece_{k}_location_nll']=nll;sums['hidden_location_nll']+=nll
    return sums,counts


def extend_totals(base):
    class BeliefTotals(base):
        def add(self,d,log_policy,danger,belief,value):
            super().add(d,log_policy,danger,belief,value)
            if d['belief_valid']:
                extra,empty=components(belief,d['belief_mask'],d['belief'])
                self.counts['hidden_empty_squares']+=empty
                for key,value in extra.items():self.sums[key]+=value
        def summary(self,include_roc=True):
            out=super().summary(include_roc)
            out['metrics'].update({k:self.sums[k]/self.counts[v] if self.counts[v] else None for k,v in DENOMINATORS.items()})
            return out
    return BeliefTotals
