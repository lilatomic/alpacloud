import json

from alpacloud.promls.fetch import FetcherURL, Parser

if __name__ == "__main__":
	t = FetcherURL("http://localhost:9402/metrics")
	print(json.dumps({k: v.__dict__ for k, v in Parser().parse(t.fetch()).items()}, indent=2))
