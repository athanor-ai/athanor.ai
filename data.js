// Auto-generated
const CALIBRATOR_DATA = {
  "models": [
    "claude-sonnet-4-6",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "mistral-large-3",
    "kimi-k2.5"
  ],
  "modelNames": {
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "kimi-k2.5": "Kimi K2.5",
    "mistral-large-3": "Mistral Large 3"
  },
  "envs": [
    {
      "id": "hw-cbmc",
      "name": "Hardware Verification",
      "desc": "Agents debug and formally verify hardware designs against temporal and safety properties.",
      "tasks": [
        {
          "n": "Fix TLB Ctrl",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.75,
          "s": 10.0,
          "f": [
            1.0,
            1.0,
            0.0243,
            0.0,
            1.0
          ]
        },
        {
          "n": "Fix FIFO Async",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.75,
          "s": 8.0,
          "f": [
            0.4857,
            0.4857,
            0.078,
            0.078,
            0.078
          ]
        },
        {
          "n": "Fix ARB Lock",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.65,
          "s": 8.0,
          "f": [
            0.1493,
            1.0,
            0.1493,
            0.1493,
            0.1493
          ]
        }
      ]
    },
    {
      "id": "lean",
      "name": "Theorem Proving",
      "desc": "Agents construct formal proofs covering compiler correctness, data structure invariants, and abstract algebra.",
      "tasks": [
        {
          "n": "Merge Sorted",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.55,
          "s": 8.0,
          "f": [
            1.0,
            1.0,
            1.0,
            0.0,
            1.0
          ]
        },
        {
          "n": "Nat Induction Hard",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.5,
          "s": 8.0,
          "f": [
            0.6971,
            1.0,
            1.0,
            0.0,
            1.0
          ]
        },
        {
          "n": "Binary Search",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.55,
          "s": 8.0,
          "f": [
            0.0,
            1.0,
            1.0,
            1.0,
            1.0
          ]
        }
      ]
    },
    {
      "id": "csparse",
      "name": "Systems Migration",
      "desc": "Agents port numerical computing libraries to a memory-safe language with formal verification.",
      "tasks": [
        {
          "n": "Norm",
          "d": "Port a numerical computing function to a verified implementation.",
          "c": 0.5,
          "s": 8.0,
          "f": [
            0.4998,
            0.4676,
            0.0,
            0.2371,
            0.2367
          ]
        },
        {
          "n": "Usolve",
          "d": "Port a numerical computing function to a verified implementation.",
          "c": 0.5,
          "s": 8.0,
          "f": [
            0.4249,
            0.3511,
            0.0,
            0.2608,
            0.3736
          ]
        },
        {
          "n": "Matvec",
          "d": "Port a numerical computing function to a verified implementation.",
          "c": 0.5,
          "s": 8.0,
          "f": [
            0.3364,
            0.3443,
            0.2387,
            0.3487,
            0.0
          ]
        }
      ]
    },
    {
      "id": "congestion",
      "name": "Network Protocols",
      "desc": "Agents implement and fix congestion control algorithms, verified against performance and fairness targets.",
      "tasks": [
        {
          "n": "Fix Cubic Slow Start",
          "d": "Fix a network protocol to meet performance targets.",
          "c": 0.9,
          "s": 8.0,
          "f": [
            0.7583,
            0.7583,
            0.7583,
            0.7583,
            0.0014
          ]
        },
        {
          "n": "Implement Fast Recovery",
          "d": "Implement a network protocol from scratch.",
          "c": 0.94,
          "s": 8.0,
          "f": [
            0.5011,
            0.002,
            0.5291,
            0.5291,
            0.5291
          ]
        },
        {
          "n": "Fix AIMD",
          "d": "Fix a network protocol to meet performance targets.",
          "c": 0.85,
          "s": 8.0,
          "f": [
            0.3007,
            0.3007,
            0.0,
            0.3007,
            0.3007
          ]
        }
      ]
    },
    {
      "id": "consensus",
      "name": "Distributed Systems",
      "desc": "Agents build and repair consensus protocols, verified against safety and liveness specifications.",
      "tasks": [
        {
          "n": "Fix Consistent Hash Replication",
          "d": "Fix bugs in a distributed protocol implementation.",
          "c": 0.85,
          "s": 8.0,
          "f": [
            1.0,
            1.0,
            0.0,
            0.7787,
            0.0
          ]
        },
        {
          "n": "Log Compaction",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.45,
          "s": 8.0,
          "f": [
            0.682,
            0.682,
            0.0,
            0.0,
            0.682
          ]
        },
        {
          "n": "Fix Snapshot Replication",
          "d": "Fix bugs in a distributed protocol implementation.",
          "c": 0.8,
          "s": 8.0,
          "f": [
            0.3063,
            0.0,
            0.0,
            0.0,
            0.0
          ]
        }
      ]
    },
    {
      "id": "cedar",
      "name": "Authorization",
      "desc": "Agents write and verify authorization policies against security property specifications.",
      "tasks": [
        {
          "n": "Fix Ip Time Geo Policies",
          "d": "Fix bugs in an authorization policy system.",
          "c": 0.87,
          "s": 8.0,
          "f": [
            1.0,
            0.5776,
            0.5776,
            0.5776,
            0.0
          ]
        },
        {
          "n": "Debug Recursive Hierarchy Access",
          "d": "Build or verify authorization policies.",
          "c": 0.9,
          "s": 8.0,
          "f": [
            0.5812,
            0.7244,
            0.0,
            0.7244,
            0.5812
          ]
        },
        {
          "n": "Implement And Verify Refactoring",
          "d": "Write formal proofs that a verifier accepts.",
          "c": 0.3,
          "s": 8.0,
          "f": [
            0.3361,
            0.0,
            0.0,
            0.3561,
            0.0
          ]
        }
      ]
    }
  ]
};
