# Filament main type
FILAMENT_PROTO_MAIN_TYPE_RESERVED               = 0
FILAMENT_PROTO_MAIN_TYPE_PLA                    = 1
FILAMENT_PROTO_MAIN_TYPE_PETG                   = 2
FILAMENT_PROTO_MAIN_TYPE_ABS                    = 3
FILAMENT_PROTO_MAIN_TYPE_TPU                    = 4
FILAMENT_PROTO_MAIN_TYPE_PVA                    = 5

FILAMENT_PROTO_MAIN_TYPE_MAPPING = {
    FILAMENT_PROTO_MAIN_TYPE_PLA:       "PLA",
    FILAMENT_PROTO_MAIN_TYPE_PETG:      "PETG",
    FILAMENT_PROTO_MAIN_TYPE_ABS:       "ABS",
    FILAMENT_PROTO_MAIN_TYPE_TPU:       "TPU",
    FILAMENT_PROTO_MAIN_TYPE_PVA:       "PVA",
    FILAMENT_PROTO_MAIN_TYPE_RESERVED:  "Reserved"
}

#Filament sub type
FILAMENT_PROTO_SUB_TYPE_RESERVED                = 0
FILAMENT_PROTO_SUB_TYPE_BASIC                   = 1
FILAMENT_PROTO_SUB_TYPE_MATTE                   = 2
FILAMENT_PROTO_SUB_TYPE_SNAPSPEED               = 3
FILAMENT_PROTO_SUB_TYPE_SILK                    = 4
FILAMENT_PROTO_SUB_TYPE_SUPPORT                 = 5
FILAMENT_PROTO_SUB_TYPE_HF                      = 6
FILAMENT_PROTO_SUB_TYPE_95A                     = 7
FILAMENT_PROTO_SUB_TYPE_95A_HF                  = 8

FILAMENT_PROTO_SUB_TYPE_MAPPING = {
    FILAMENT_PROTO_SUB_TYPE_BASIC:        "Basic",
    FILAMENT_PROTO_SUB_TYPE_MATTE:        "Matte",
    FILAMENT_PROTO_SUB_TYPE_SNAPSPEED:    "SnapSpeed",
    FILAMENT_PROTO_SUB_TYPE_SILK:         "Silk",
    FILAMENT_PROTO_SUB_TYPE_SUPPORT:      "Support",
    FILAMENT_PROTO_SUB_TYPE_HF:           "HF",
    FILAMENT_PROTO_SUB_TYPE_95A:          "95A",
    FILAMENT_PROTO_SUB_TYPE_95A_HF:       "95A HF",
    FILAMENT_PROTO_SUB_TYPE_RESERVED:     "Reserved"
}

# Filament color nums
FILAMENT_PROTO_COLOR_NUMS_MAX                   = 5

# Filament Tag type
FILAMENT_PROTO_TAG_M1                           = 'M1_1K'

# M1 card protocol
M1_PROTO_TOTAL_SIZE                             = 1024
## position : section_num * 64 + block_nom * 16 + byte_num
# Section 0
M1_PROTO_UID_POS                                = (0 * 64 + 0 * 16 + 0)
M1_PROTO_UID_LEN                                = (4)
M1_PROTO_VENDOR_POS                             = (0 * 64 + 1 * 16 + 0)
M1_PROTO_VENDOR_LEN                             = (16)
M1_PROTO_MANUFACTURER_POS                       = (0 * 64 + 2 * 16 + 0)
M1_PROTO_MANUFACTURER_LEN                       = (16)
# Section 1
M1_PROTO_VERSION_POS                            = (1 * 64 + 0 * 16 + 0)
M1_PROTO_VERSION_LEN                            = (2)
M1_PROTO_MAIN_TYPE_POS                          = (1 * 64 + 0 * 16 + 2)
M1_PROTO_MAIN_TYPE_LEN                          = (2)
M1_PROTO_SUB_TYPE_POS                           = (1 * 64 + 0 * 16 + 4)
M1_PROTO_SUB_TYPE_LEN                           = (2)
M1_PROTO_TRAY_POS                               = (1 * 64 + 0 * 16 + 6)
M1_PROTO_TRAY_LEN                               = (2)
M1_PROTO_COLOR_NUMS_POS                         = (1 * 64 + 0 * 16 + 8)
M1_PROTO_COLOR_NUMS_LEN                         = (1)
M1_PROTO_ALPHA_POS                              = (1 * 64 + 0 * 16 + 9)
M1_PROTO_ALPHA_LEN                              = (1)
M1_PROTO_MULTI_MODE_POS                         = (1 * 64 + 0 * 16 + 10)
M1_PROTO_MULTI_MODE_LEN                         = (1)
M1_PROTO_RGB_1_POS                              = (1 * 64 + 1 * 16 + 0)
M1_PROTO_RGB_1_LEN                              = (3)
M1_PROTO_RGB_2_POS                              = (1 * 64 + 1 * 16 + 3)
M1_PROTO_RGB_2_LEN                              = (3)
M1_PROTO_RGB_3_POS                              = (1 * 64 + 1 * 16 + 6)
M1_PROTO_RGB_3_LEN                              = (3)
M1_PROTO_RGB_4_POS                              = (1 * 64 + 1 * 16 + 9)
M1_PROTO_RGB_4_LEN                              = (3)
M1_PROTO_RGB_5_POS                              = (1 * 64 + 1 * 16 + 12)
M1_PROTO_RGB_5_LEN                              = (3)
M1_PROTO_SKU_POS                                = (1 * 64 + 2 * 16 + 0)
M1_PROTO_SKU_LEN                                = (4)
# Section 2
M1_PROTO_DIAMETER_POS                           =( 2 * 64 + 0 * 16 + 0)
M1_PROTO_DIAMETER_LEN                           = (2)
M1_PROTO_WEIGHT_POS                             = (2 * 64 + 0 * 16 + 2)
M1_PROTO_WEIGHT_LEN                             = (2)
M1_PROTO_LENGTH_POS                             = (2 * 64 + 0 * 16 + 4)
M1_PROTO_LENGTH_LEN                             = (2)
M1_PROTO_DRY_TEMP_POS                           = (2 * 64 + 1 * 16 + 0)
M1_PROTO_DRY_TEMP_LEN                           = (2)
M1_PROTO_DRY_TIME_POS                           = (2 * 64 + 1 * 16 + 2)
M1_PROTO_DRY_TIME_LEN                           = (2)
M1_PROTO_HOTEND_MAX_TEMP_POS                    = (2 * 64 + 1 * 16 + 4)
M1_PROTO_HOTEND_MAX_TEMP_LEN                    = (2)
M1_PROTO_HOTEND_MIN_TEMP_POS                    = (2 * 64 + 1 * 16 + 6)
M1_PROTO_HOTEND_MIN_TEMP_LEN                    = (2)
M1_PROTO_BED_TYPE_POS                           = (2 * 64 + 1 * 16 + 8)
M1_PROTO_BED_TYPE_LEN                           = (2)
M1_PROTO_BED_TEMP_POS                           = (2 * 64 + 1 * 16 + 10)
M1_PROTO_BED_TEMP_LEN                           = (2)
M1_PROTO_FIRST_LAYER_TEMP_POS                   = (2 * 64 + 1 * 16 + 12)
M1_PROTO_FIRST_LAYER_TEMP_LEN                   = (2)
M1_PROTO_OTHER_LAYER_TEMP_POS                   = (2 * 64 + 1 * 16 + 14)
M1_PROTO_OTHER_LAYER_TEMP_LEN                   = (2)
M1_PROTO_MF_DATE_POS                            = (2 * 64 + 2 * 16 + 0)
M1_PROTO_MF_DATE_LEN                            = (8)
M1_PROTO_RSA_KEY_VER_POS                        = (2 * 64 + 2 * 16 + 8)
M1_PROTO_RSA_KEY_VER_LEN                        = 2

# ERROR CODE
FILAMENT_PROTO_OK                               = 0
FILAMENT_PROTO_ERR                              = -1
FILAMENT_PROTO_PARAMETER_ERR                    = -2
FILAMENT_PROTO_RSA_KEY_VER_ERR                  = -3
FILAMENT_PROTO_SIGN_CHECK_ERR                   = -4

SNAPMAKER_SALT_HASH = "19aee31a8bcadb0becc08bbaa9197ab403f9c7a2097197d127a2ab7010a7867a"

FILAMENT_PROTO_RSA_PUBLIC_KEY_0 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA8oEF7YuKO863TbUxnrvY
H1JFrvCnMapm8Ho952KlfNWbf6IEDMlX6QJpBuvUkrkjWpLJJQurIWL3KFeLUhCh
POrYdiGrdsUlp4YO037iLSlgmzo1dUdgbawAcGox1PvR/Naw5ADibubO2rN49WQR
+BkxxigvoWHSFetaoMCswQ5B/niq3byhzktgmWOcv71F4yFwcxivF8R+s0gSBL4i
/1zNeSUZkbvP4/T0B08i3D+e6fl9xpCnINZ3P9OWcx+p3SB2o4TdmAeKV4hkT9n7
o+/OWr92fx6qbiNKJr04oMhrRsFK6w7hitp2n8RGS64w9lhtplnBgxtbgxAYyUnp
qwIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_1 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA8nbtQNABbc5PkyzI0A5m
VH/E8y23Wld0iykvTOoBYJOrPwJDmXsnSyyX84Nv6voSr8FYv3Fb2SqSdOgQLFqp
BXvntXew8rPpq5Ll8gSzLRxE1VmEOVtZWCTJ4Wxwwi79rrFmpa/nAtUeYZIGiiud
w2MzCHXW5G3c1FWhQ0C8vUUMfBQXmGnoHGsul6R8xld6CDCWY8ia/FvfR+KCtMRn
VYyYguYsq4rODWJHiFCOef4FZconUR3RTh0ojvq78CsHk94goxidWzZoKcVnvWhh
bOixTjU37W4JDECEOui3ObMMvJkzxkZo1irlAH7jTiPqhP94U/JbRDpBlHOOn67b
GQIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_2 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxZQPYewwMFaPlcEHq+SH
QS1C1NhVmAaY56qxLyHJ4aNc2iWdCx4/9ZKY4CL6xkeCD88Zndv/xzImplRdoAzo
whD47Vm4iuq8+NqHUI8na6ISd+MZ/O6/eo/ggaEZBX8lR+Yf0qfWtntsI9flUOoJ
mq1IXvNXqOxflUmPyffT40QSkAN4Rr3scB3ozlxuJZehWM/lUmZ1H5PQDwAqsM0T
Rj6ChzVmUbSvwEvbDTwpXkpMA0C5//OW0T//IKDEBYxEl928vYbraLRDRIetgdaD
o+77+ztfOv4AyP/ipikprHwIWi7yga5KUXq/XpNPy6cPISZD+/LBUJBxLELspREP
rQIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_3 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvK8cJyeFeTkFgkSLCCAg
EgR9KAvIHmvK8CRdtn+W6PiIbN04MFIg8jiYW/3fq+AcBFFMo+HtR2gym8JNVx2I
RDI4WdfbR/0gaIHjOQ41OwlXmqqSkDsFmjxVI6bDRZYpHkOfkC+9Vi1Aii4l/Yq9
O7s+2j4zP9GoUWWJPb3mW07Vu+EnHB/XIuaoDJVQAS+ov3xTotCeKdcdgySnNP5g
kOvWUvWtwNQldCRcQ0eo3j5RO+4J4IRK2J8q7BrdV/gbJUE/BBPIOuURPLzNJJO3
wgx4PEwlb5uYEUL35ARL7NzL8ZOxebzs5H4tXuWrBhALw6O33Tfg3TmTmwR2JUpv
7QIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_4 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvafhk7Bdb3F+5B9w7YXv
chrNzl09QkZc27NLxL0ViRitGQhX9KC/xVg+XkBGI8XfioAwYkJ3jYgwmci5gJOL
ofPyNXcFtvtzq2NZNuDZY26krrXLORhS1o8ue92RB2gM92Rc2heWVrsvLycNl2Qz
OUjUEGmWpSMo98xIsgkTZJ4aYxWVN86yqknOcHVpTmcr5SBRB90K9hTRtsaMD97O
FYVc7AA/TGwqFJOnXXzWczWtg7kUY2vqCHwsvKs3G/EIFKOIe1n37V94OcxHTySC
co9Kc6Y0bGFIwIruinH1WkFVt6TAzo+0ZdZy5Sq493AG9y1RZ5nYj5qUmc1PMmrD
gwIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_5 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxWdxd7qeouSFbZ2Sldv3
apDrgAupOYiDRkO85C+qkZaezOzqW0EsOV0x7nG/smw++TRfHyGIK4gXCdg1JfNR
WYjqckRdnLYMzGdDk24VV5Bbrsgska0v0Oy1ucz3CYu+F22ais00OqK0MY0B96MI
/B/0pRSTAIyxvC6LjhHy8DYyPdqNF9EMikKfAfcn7ytsH1PoSSGVtrZqyNe5OLrW
yAw+FQsTg/VFJcYxPTQJ1ymwQmDCdKgApe3PVajyYswoIA7R0S8ujau0aAFEO3dU
GDEwjOnaHfwFlg3OKMFJTxc2sl/WEB8xtWuKl0Guf0VnzWJ6noxqf/DiaN1fuHG0
AwIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_6 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqF+YJNHLHC6c25oTDgNg
liahUxWBPSkgght1/gJu5vBRDKWEn6i/RuKAFdTOsH+Hlvr5qWms7bBUHx78UMF+
FF1Nq9tb4jhFuqq4HWsBBjNnU6O0JhFTjKJU2nudmphXlpdLQfcKSIYMQe795GHL
izh8WsNTcTHNNBkjhi7y4c4RUqnJso0L6vrf0B3EB/9DDUJitrwfw+1/OrKOEVEP
624sEa802cHfb+BG9zKBXjFwzYCYF9gWey9yeA3UA7EYmPpqA1lqNv8m0r7YjZ4n
uGBDjs+AXaGtdqrW3IUtkUF2vWwNSRncbcXi3mNfzslrtPhsDVAFki4vDSw7yNht
2wIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_7 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuKWRCTTgxPltfflWHdhu
2ITxWC/LTEl7OtatNWFhMFQZF2J5SN/45bjH6xIPTcDglTSl2/UMC1D/ugiq+j0z
dGSdE7xn3ZSzLTMCwgRkvXmd8aQgafBYbB7E6oAgus+6lRXZPwnMfZAe0yaJNHyt
1Wd8ZUlRY7BHSPPtmG1liVEzxoTb6urB6mK49r24+oC7xa65q5NSdlZWSTeaK4Xt
DVVDiwe+uubNTm59KnVAKgBMNd3qN942pH6fo/dBz++BzJVEG/qJewHUTGZAeIl+
CgqhSEbmEIgolsDgaKY99ZWa2FWJdo+ohYhmjc92TyB9kWw6yIwez+tlRUkssLGt
SwIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_8 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt7XOTs6P2xB8v8/xWVdR
wVefphRDXSuv74RObtr0pwLTc7BytkcDw8r60BNPv9hGDpW2S1szxqS8x4EaOHP7
81qNpIUULlUdXxty1RvpSdfRb044kpwl7A/s4OEakkyJZF1ed+Qte1FqOFDDIZ+l
g+Co8FjOwWixoSyIlR22mEP7r6Y98GL5tnSohkVoGAgEipswWb6549mssjZmES+J
hB0axY6Dl/LlDYxN6jjUZwSIo7bw0GXGm9ScW2qTVaT1m2A9etpD6OIG+iQVLQqP
whVBs5q0o/EM4nBN88RBsF2OmfkcZPJ2NdX6o3qx+pCZ9NDgkHjGDZdnGEnM5Lu2
dwIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_9 = b"""
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz/d5C5FpqlcF7NbUEvBN
fiDJWH0BF63PEwHPiX+cS6l+q4NqqYI167u1pGkZGJV1njgGYFTM08x2KO7/bk6o
CWcGuKWNM8Tp1+tv3XioNGVCnIpHmdUx5F9qcXlPtDx74wQk/+JZLQ/sLnLvHcV3
YTaz55fpyzVUHkgXusdVynSyAt3ywWWQRcjp3sspGa/udC0j6LCvrzqLACv3gMGA
Id0b6REzjSn03UzkwBIwSb8DszieeNhaCOK4M/TxPFNyrhQRYcAvhiZJu+tylqJs
VP+gaWFvElFeFkxcHvYXHdJPlJLjYeT51hm/pdll26yYLhpeBa0inHwSqv4D3jFZ
PQIDAQAB
-----END RSA PUBLIC KEY-----"""

FILAMENT_PROTO_RSA_PUBLIC_KEY_MAPPING = {
    0: FILAMENT_PROTO_RSA_PUBLIC_KEY_0,
    1: FILAMENT_PROTO_RSA_PUBLIC_KEY_1,
    2: FILAMENT_PROTO_RSA_PUBLIC_KEY_2,
    3: FILAMENT_PROTO_RSA_PUBLIC_KEY_3,
    4: FILAMENT_PROTO_RSA_PUBLIC_KEY_4,
    5: FILAMENT_PROTO_RSA_PUBLIC_KEY_5,
    6: FILAMENT_PROTO_RSA_PUBLIC_KEY_6,
    7: FILAMENT_PROTO_RSA_PUBLIC_KEY_7,
    8: FILAMENT_PROTO_RSA_PUBLIC_KEY_8,
    9: FILAMENT_PROTO_RSA_PUBLIC_KEY_9,
}