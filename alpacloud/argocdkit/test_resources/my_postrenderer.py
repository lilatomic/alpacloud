#!/usr/bin/env python3
from alpacloud.argocdkit.postrender import postrenderer
from alpacloud.lens.k8s import Item, labels
from alpacloud.lens.models import CombinedBoundLens, Const, ForeachLens, LensT, korn

every_svc: LensT = ForeachLens(Item("service"))

svc_loadbalanced = CombinedBoundLens(
	(
		every_svc["spec"]["type"] @ Const("LoadBalancer"),
		every_svc / labels / korn("service.beta.kubernetes.io/azure-load-balancer-internal") @ Const("true"),
	)
)

p = postrenderer(
	CombinedBoundLens(
		(
			ForeachLens(labels / korn("my-label")) @ Const("my-label-value"),
			svc_loadbalanced,
		)
	)
)

if __name__ == "__main__":
	p()
