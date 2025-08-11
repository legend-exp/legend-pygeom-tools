(gdml-metadata)=

# Metadata stored into GDML

## Detector metadata

Detector metadata is written into the userinfo section of the output GDML file.

The structure resembles a nested dictionary, stored as follows (read
`auxtype → auxvalue`. `"value"` represents a literal string):

```bash
├─ "RMG_detector" → $det_type
│  ├─ $physvol_name → $det_uid
│  └─ [...repeat...]
├─ [...repeat...]
│
└─ "RMG_detector_meta" → ""
   ├─ $physvol_name → json($metadata)
   └─ [...repeat...]
```

## Coloring for visualization

The color is directly attached as auxiliary data to the logical volumes:

```bash
└─ "rmg_color" → "-1" || "$r,$g,$b,$a" # components between 0 and 1
```
