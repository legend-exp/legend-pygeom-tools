(gdml-metadata)=

# Metadata stored into GDML

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
