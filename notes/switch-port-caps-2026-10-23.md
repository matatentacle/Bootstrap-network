# Switch-port bandwidth limits vs firewall caps

Audit 23 Oct 2026 from the 14 Oct switch running-configs (14 GS1920s read over SSH), the ATP500
running-config of 13 Oct and the FortiGate figures in the crossref register. Read-only; nothing
changed. Context: Bootstrap used to set tenant caps as per-port bandwidth-limit on the switches
(Nebula) instead of on the firewall; Mat has seen these cause bad packet loss, so the policy is to
remove them as they are found, each removal with Mat's OK (23 Oct 2026).

ZyNOS semantics: `bandwidth-limit ingress <kbps>` sets a rate, the bare `bandwidth-limit ingress`
line enables it (same for egress). On an access port, ingress = tenant upload, egress = tenant
download. 'FW cap' is the ATP500 BWM rule for the port's PVID shown as down/up, or the FortiGate
interface outbandwidth. Link state is from 14 Oct, so SW12 port 2 shows Down although it is up now.

Totals: 53 ports with an ACTIVE per-port limit, 43 ports with a rate configured
but not enabled (dormant). Switches with no bandwidth-limit lines at all: SW10, SW11.

## A. Inter-switch links with a cap (remove first)

A policer on a link that carries several tenants' VLANs hurts everyone behind it at once.

switch ip            port link   pvid sw up/down  FW cap                 tenant / why
SW02   192.168.1.38  2    1G/F        200M/200M                          
                                                                         -> INTER-SWITCH LINK CAPPED (to GS1350 192.168.1.46 (FHG2))
SW15   192.168.1.37  1    1G/F   46   50M/50M     102M/102M+burst        vlan46_AcmeFireCult
                                                                         -> INTER-SWITCH LINK CAPPED (to GS1350 192.168.46.4 (Bar Switch SW16))

## B. Access ports where the switch cap is lower than the firewall cap (tenant feels these)

The tenant gets the switch figure, not the firewall figure, and the switch drops rather than shapes.

switch ip            port link   pvid sw up/down  FW cap                 tenant / why
SW01   192.168.1.39  1    1G/F   10   50M/50M     100M/100M              Vlan10_BootStrap
                                                                         -> switch is the binding cap: download 50M vs FW 100M, upload 50M vs FW 100M
SW01   192.168.1.39  3    Down   10   50M/50M     100M/100M              Vlan10_BootStrap
                                                                         -> switch is the binding cap: download 50M vs FW 100M, upload 50M vs FW 100M
SW01   192.168.1.39  6    1G/F   10   50M/50M     100M/100M              Vlan10_BootStrap
                                                                         -> switch is the binding cap: download 50M vs FW 100M, upload 50M vs FW 100M
SW01   192.168.1.39  16   1G/F   42   30M/30M     256M/256M              Vlan42_FormFormForm_ltd
                                                                         -> switch is the binding cap: download 30M vs FW 256M, upload 30M vs FW 256M
SW05   192.168.1.41  14   1G/F   38   30M/30M     102M/102M              Vlan38_Pinzutu_Films
                                                                         -> switch is the binding cap: download 30M vs FW 102M, upload 30M vs FW 102M
SW08   192.168.1.36  17   1G/F   55   60M/60M     102M/102M              Vlan55_Studio_Cw208
                                                                         -> switch is the binding cap: download 60M vs FW 102M, upload 60M vs FW 102M
SW09   192.168.1.44  1    1G/F   64   100M/100M   256M/256M              Vlan64_TheDustyKnuckleR1
                                                                         -> switch is the binding cap: download 100M vs FW 256M, upload 100M vs FW 256M
SW15   192.168.1.37  6    1G/F   46   50M/50M     102M/102M+burst        vlan46_AcmeFireCult
                                                                         -> switch is the binding cap: download 50M vs FW 102M, upload 50M vs FW 102M

## C. Access ports where the switch is the only cap

Removing these uncaps the tenant unless a firewall rule is added first (FortiGate tenants: add shaping on the FortiGate, or decide not to cap).

switch ip            port link   pvid sw up/down  FW cap                 tenant / why
SW13   192.168.1.45  4    1G/F   156  30M/30M     none on FortiGate      PH3.17-18A - Harp-E
                                                                         -> switch is the ONLY cap
SW13   192.168.1.45  8    100M/F 72   100M/100M   NO BWM RULE            Vlan72_AshfordSon
                                                                         -> switch is the ONLY cap

## D. Duplicates of the firewall cap (same figure on both)

No bandwidth change when removed; still worth removing because of the packet-loss behaviour.

switch ip            port link   pvid sw up/down  FW cap                 tenant / why
SW01   192.168.1.39  4    Down   34   30M/30M     31M/31M                Vlan34_SistahSpace
                                                                         -> duplicate of FW cap (same figure)
SW02   192.168.1.38  7    1G/F   71   60M/60M     61M/61M                Vlan71_CafeOTO
                                                                         -> duplicate of FW cap (same figure)
SW05   192.168.1.41  13   1G/F   49   100M/100M   102M/102M              Vlan49_StudioArchetype
                                                                         -> duplicate of FW cap (same figure)
SW06   192.168.1.34  1    1G/F   154  60M/60M     58M (FG outbandwidth)  FH2.11 - 01-Profiles Ltd/ Gunga
                                                                         -> duplicate of FW cap (same figure)
SW06   192.168.1.34  2    1G/F   35   60M/60M     61M/61M                Vlan35_NewcomerWines
                                                                         -> duplicate of FW cap (same figure)
SW07   192.168.1.40  2    Down   16   100M/100M   102M/102M              Vlan16_Fair_Finance
                                                                         -> duplicate of FW cap (same figure)
SW07   192.168.1.40  3    Down   16   100M/100M   102M/102M              Vlan16_Fair_Finance
                                                                         -> duplicate of FW cap (same figure)
SW07   192.168.1.40  4    Down   16   100M/100M   102M/102M              Vlan16_Fair_Finance
                                                                         -> duplicate of FW cap (same figure)
SW07   192.168.1.40  5    Down   16   100M/100M   102M/102M              Vlan16_Fair_Finance
                                                                         -> duplicate of FW cap (same figure)
SW07   192.168.1.40  6    Down   16   100M/100M   102M/102M              Vlan16_Fair_Finance
                                                                         -> duplicate of FW cap (same figure)
SW08   192.168.1.36  3    100M/F 54   100M/100M   102M/102M              vlan54_Thamesreach
                                                                         -> duplicate of FW cap (same figure)
SW08   192.168.1.36  7    1G/F   50   500M/500M   512M/512M              Vlan50_AdamAftanas
                                                                         -> duplicate of FW cap (same figure)
SW08   192.168.1.36  11   Down   54   100M/100M   102M/102M              vlan54_Thamesreach
                                                                         -> duplicate of FW cap (same figure)
SW08   192.168.1.36  12   Down   54   100M/100M   102M/102M              vlan54_Thamesreach
                                                                         -> duplicate of FW cap (same figure)
SW08   192.168.1.36  13   100M/F 26   30M/30M     31M/31M                Vlan26_LiveThroughThis
                                                                         -> duplicate of FW cap (same figure)
SW08   192.168.1.36  24   Down   54   100M/100M   102M/102M              vlan54_Thamesreach
                                                                         -> duplicate of FW cap (same figure)
SW09   192.168.1.44  4    Down   48   100M/100M   102M/102M              Vlan48_FieldVision
                                                                         -> duplicate of FW cap (same figure)
SW09   192.168.1.44  6    1G/F   48   100M/100M   102M/102M              Vlan48_FieldVision
                                                                         -> duplicate of FW cap (same figure)
SW12   192.168.1.33  1    1G/F   10   100M/100M   100M/100M              Vlan10_BootStrap
                                                                         -> duplicate of FW cap (same figure)
SW12   192.168.1.33  9    1G/F   56   250M/250M   256M/256M              Vlan56_OpenDemocracy
                                                                         -> duplicate of FW cap (same figure)
SW12   192.168.1.33  13   Down   53   30M/30M     31M/31M                Vlan53_BridgeTheGap
                                                                         -> duplicate of FW cap (same figure)
SW13   192.168.1.45  7    1G/F   32   30M/30M     31M/31M                Vlan32_10pm_Studio
                                                                         -> duplicate of FW cap (same figure)
SW15   192.168.1.37  4    1G/F   66   30M/30M     31M/31M                Vlan66_StudioMcDonnell
                                                                         -> duplicate of FW cap (same figure)

## E. Switch cap higher than the firewall cap

Firewall wins today; harmless, remove when convenient.

switch ip            port link   pvid sw up/down  FW cap                 tenant / why
SW06   192.168.1.34  10   Down   158  250M/250M   97M (FG outbandwidth)  Fair Finance
                                                                         -> switch cap above FW cap (FW wins)
SW07   192.168.1.40  12   1G/F   155  250M/250M   97M (FG outbandwidth)  FHG1 - Colab
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  1    1G/F   21   250M/250M   205M/205M              Vlan21_Compost_Creative
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  4    Down   12   100M/100M   80M/20M                Vlan12_bars
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  5    100M/F 44   100M/100M   31M/31M                Vlan44_vbqspeakers
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  10   1G/F   41   60M/60M     51M/51M                Vlan41_The_Raze_Collective
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  15   1G/F   39   100M/100M   31M/31M                Scoff_Studios
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  16   Down   39   100M/100M   31M/31M                Scoff_Studios
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  18   Down   12   100M/100M   80M/20M                Vlan12_bars
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  19   Down   12   100M/100M   80M/20M                Vlan12_bars
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  20   1G/F   12   100M/100M   80M/20M                Vlan12_bars
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  21   1G/F   12   100M/100M   80M/20M                Vlan12_bars
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  22   1G/F   12   100M/100M   80M/20M                Vlan12_bars
                                                                         -> switch cap above FW cap (FW wins)
SW08   192.168.1.36  23   1G/F   12   100M/100M   80M/20M                Vlan12_bars
                                                                         -> switch cap above FW cap (FW wins)
SW12   192.168.1.33  2    Down   13   60M/60M     40M/10M                Vlan13_BootstrapCR
                                                                         -> switch cap above FW cap (FW wins)
SW15   192.168.1.37  2    100M/F 17   100M/100M   51M/51M                Vlan17_40tf_Brewery
                                                                         -> switch cap above FW cap (FW wins)
SW15   192.168.1.37  3    Down   17   100M/100M   51M/51M                Vlan17_40tf_Brewery
                                                                         -> switch cap above FW cap (FW wins)
SW15   192.168.1.37  5    100M/F 17   100M/100M   51M/51M                Vlan17_40tf_Brewery
                                                                         -> switch cap above FW cap (FW wins)

## Dormant: rate configured, limit not enabled

Harmless today. Clear them when the port is touched so nobody enables them by accident.

switch ip            port link   pvid rate        FW cap                 tenant
SW02   192.168.1.38  4    1G/F   10   250M/250M   100M/100M              Vlan10_BootStrap
SW02   192.168.1.38  5    1G/F   64   250M/250M   256M/256M              Vlan64_TheDustyKnuckleR1
SW03   192.168.1.47  1    100M/F 52   100M/100M   102M/102M              Vlan52_NordCityltd
SW03   192.168.1.47  2    1G/F   14   100M/100M   102M/102M              Vlan14_Tenticle
SW03   192.168.1.47  3    Down        250M/250M                          
SW03   192.168.1.47  4    1G/F   20   100M/100M   256M/256M              Vlan20_Julia_Brenard
SW03   192.168.1.47  5    1G/F   34   30M/30M     31M/31M                Vlan34_SistahSpace
SW03   192.168.1.47  7    1G/F   58   100M/100M   102M/1024M             Vlan58_Mediorite
SW03   192.168.1.47  10   1G/F   51   30M/30M     31M/31M                Vlan51_HelenKerridge
SW03   192.168.1.47  11   1G/F   74   100M/100M   102M/102M              Vlan74_WisemartSolicitors
SW03   192.168.1.47  12   1G/F   73   100M/100M   102M/102M              Vlan73_MAKE
SW03   192.168.1.47  14   1G/F   62   30M/30M     61M/61M                Vlan62_ProjectsOffice
SW03   192.168.1.47  15   1G/F   34   30M/30M     31M/31M                Vlan34_SistahSpace
SW03   192.168.1.47  16   1G/F   157  30M/30M     none on FortiGate      PH1.14 - Henry Playfoot
SW03   192.168.1.47  17   100M/F 27   30M/30M     512M/512M              Vlan27_DGN_Studio
SW04   192.168.1.35  1    Down        60M/60M                            
SW04   192.168.1.35  3    1G/F   69   100M/100M   102M/102M              Vlan69_LAWA
SW04   192.168.1.35  4    Down        100M/100M                          
SW04   192.168.1.35  5    1G/F   24   60M/60M     61M/61M                Vlan24_Lickerish
SW04   192.168.1.35  6    1G/F   36   30M/30M     31M/31M                Vlan_36_Neighbourhood_Studio
SW04   192.168.1.35  7    1G/F   69   100M/100M   102M/102M              Vlan69_LAWA
SW04   192.168.1.35  8    10M/F  159  30M/30M     none on FortiGate      St Paul's Waldorf School
SW04   192.168.1.35  10   1G/F   159  30M/30M     none on FortiGate      St Paul's Waldorf School
SW04   192.168.1.35  11   Down        100M/100M                          
SW04   192.168.1.35  12   1G/F   152  102M/102M   97M (FG outbandwidth)  PH2.3 - Curamcare
SW04   192.168.1.35  13   1G/F   69   100M/100M   102M/102M              Vlan69_LAWA
SW04   192.168.1.35  14   Down        100M/100M                          
SW04   192.168.1.35  16   1G/F   67   100M/100M   102M/102M              Vlan67_SilverfishProductions
SW05   192.168.1.41  1    1G/F   18   50M/50M     51M/51M                Vlan18_Arnie_Productions
SW05   192.168.1.41  2    Down        61M/61M                            
SW05   192.168.1.41  4    Down   10   50M/50M     100M/100M              Vlan10_BootStrap
SW05   192.168.1.41  5    1G/F   37   60M/60M     61M/61M                VLAN37_Wazzo_LTD
SW05   192.168.1.41  6    100M/F 10   60M/60M     100M/100M              Vlan10_BootStrap
SW05   192.168.1.41  8    1G/F   150  100M/100M   146M (FG outbandwidth) CW207 - Create London
SW05   192.168.1.41  9    Down   38   30M/30M     102M/102M              Vlan38_Pinzutu_Films
SW05   192.168.1.41  11   1G/F   60   30M/30M     61M/61M                Vlan60_BalaamMurphyLtd
SW05   192.168.1.41  12   1G/F   70   60M/60M     61M/61M                Vlan70_LeadersUnlocked
SW06   192.168.1.34  3    1G/F   151  80M/80M     58M (FG outbandwidth)  FH2.1 - ReLine
SW06   192.168.1.34  6    1G/F   28   30M/30M     102M/102M              Vlan28_SarahDawes
SW06   192.168.1.34  12   1G/F   158  250M/250M   97M (FG outbandwidth)  Fair Finance
SW12   192.168.1.33  3    Down   153  250M/250M   none on FortiGate      PH3.6-8 - Cake Architecture
SW12   192.168.1.33  4    Down   153  250M/250M   none on FortiGate      PH3.6-8 - Cake Architecture
SW12   192.168.1.33  6    1G/F   153  250M/250M   none on FortiGate      PH3.6-8 - Cake Architecture

## ATP500 BWM rules worth a look

Asymmetric, under 30M, bursting, or missing while the sheet says Active.

vlan12   bwm 60  80M/20M      asymmetric; under 30M      Vlan12_bars  (sheet Inactive, 100.0 Mbps)
vlan13   bwm 57  40M/10M      asymmetric; under 30M      Vlan13_BootstrapCR  (sheet MAKE SHARED, 100.0 Mbps)
vlan22   bwm 48  20M/20M      under 30M                  Vlan22_OfficeS_M  (sheet Inactive,  Mbps)
vlan46   bwm 29  102M/102M    burst allowed              vlan46_AcmeFireCult  (sheet Active, 50.0 Mbps)
vlan47   bwm 28  51M/51M      burst allowed              Vlan47_LatinAmerica  (sheet ,  Mbps)
vlan58   bwm 18  102M/1024M   asymmetric                 Vlan58_Mediorite  (sheet Active, 100.0 Mbps)
vlan59   bwm 17  102M/1024M   asymmetric                 Vlan59_FullTimeHobbyLtd  (sheet Active, 100.0 Mbps)
vlan72   no rule               NO BWM RULE                Vlan72_AshfordSon  (sheet Active, 100.0 Mbps)

## Also seen: access ports not linking at 1G (14 Oct)

Off-topic for caps, but a 100M or 10M link is its own hard limit; usually cabling or a fixed-speed device.

SW04   192.168.1.35  port 8   10M/F
SW08   192.168.1.36  port 3   100M/F
SW08   192.168.1.36  port 5   100M/F
SW08   192.168.1.36  port 13  100M/F
SW15   192.168.1.37  port 2   100M/F
SW15   192.168.1.37  port 5   100M/F
SW07   192.168.1.40  port 7   100M/F
SW07   192.168.1.40  port 8   100M/F
SW05   192.168.1.41  port 6   100M/F
SW13   192.168.1.45  port 8   100M/F
SW13   192.168.1.45  port 20  10M/F
SW03   192.168.1.47  port 1   100M/F
SW03   192.168.1.47  port 17  100M/F
