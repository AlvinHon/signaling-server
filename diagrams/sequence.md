Sequence diagram created in [js-sequence-diagrams](https://bramp.github.io/js-sequence-diagrams/)

```text
Client A->Signaling Server: Create Offer
Client A-->Signaling Server: A's ICE Candidates
Signaling Server->Client B: Get Offer
note over Client B: Accept offer
Client B-->Signaling Server: B's ICE Candidates
Client B->Signaling Server: Create Answer
Signaling Server-->Client B: A's ICE Candidates
Signaling Server->Client A: Get Answer
Signaling Server-->Client A: B's ICE Candidates
note over Client A: Accept answer
Client A-->Client B: Data Channel Connected
```