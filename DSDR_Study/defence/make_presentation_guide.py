"""
Presentation guide: for every slide of DSDR_Presentation_Chaptered.pptx the speaker note, an explanation
in plain English and the same explanation in Nepali.  Typeset with XeLaTeX (Nirmala UI for Devanagari).

Slide pictures: defence/slides_ch/cNN.png (exported from the deck).
Output: defence/DSDR_Presentation_Guide.tex  ->  DSDR_Presentation_Guide.pdf
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

STORY_EN = [
    "A distribution feeder is protected by a recloser and by fuses on its branches. Most faults on overhead lines are temporary. So the recloser is set to trip very fast first: the fault disappears, the recloser closes again, and the fuse is not lost. This is called fuse saving.",
    "It only works if the recloser acts before the fuse starts to melt. Without a generator on the feeder this is easy, because the recloser and the fuse carry the same fault current.",
    "When a distributed generator (DG) is connected, the fuse carries the current from the grid and from the DG together, but the recloser carries only its own share. The fuse now melts sooner, the recloser does not get faster, and the fuse can melt first. A recloser in the middle of the line even sees current flowing backwards.",
    "The solution studied is the dual-setting directional recloser (DSDR). The mid-line recloser R2 gets two groups of settings: one for current coming from the grid (forward) and one for current coming from the DG (reverse). The direction of the current selects the group.",
    "I built this on the IEEE 13-node feeder in DIgSILENT PowerFactory and checked 39 combinations of fault location and fault type. Without DG, 39 of 39 are coordinated. With the DG and ordinary settings, only 24. With the DSDR and larger fuses, 38 of 39.",
    "The honest conclusion: the dual setting is necessary but not sufficient. It needs the fuse revision as well, and one case stays lost because the relay's dial cannot go any further.",
]
STORY_NE = [
    "Distribution feeder लाई recloser र शाखाहरूमा राखिएका fuse ले सुरक्षा गर्छन्। Overhead line मा हुने धेरैजसो fault अस्थायी हुन्छन्। त्यसैले recloser लाई पहिले धेरै छिटो trip गर्ने गरी मिलाइन्छ: fault हराउँछ, recloser फेरि बन्द हुन्छ, र fuse जोगिन्छ। यसलाई fuse saving भनिन्छ।",
    "यो तब मात्र काम गर्छ जब fuse पग्लन सुरु हुनुअघि नै recloser ले काम गर्छ। Feeder मा generator नहुँदा यो सजिलो हुन्छ, किनभने recloser र fuse दुवैमा उही fault current बग्छ।",
    "Distributed generator (DG) जोडेपछि fuse मा grid र DG दुवैको current सँगै बग्छ, तर recloser मा आफ्नो भागको current मात्र बग्छ। अब fuse छिटो पग्लन्छ, recloser भने छिटो हुँदैन, त्यसैले fuse पहिले पग्लन सक्छ। Line को बीचमा रहेको recloser ले त उल्टो दिशाको current समेत देख्छ।",
    "यसको समाधानका रूपमा dual-setting directional recloser (DSDR) अध्ययन गरिएको हो। बीचको recloser R2 लाई दुई समूहका setting दिइन्छ: एउटा grid बाट आउने current (forward) का लागि र अर्को DG बाट आउने current (reverse) का लागि। Current को दिशाले कुन समूह प्रयोग गर्ने भन्ने छान्छ।",
    "मैले यो विधि DIgSILENT PowerFactory मा IEEE 13-node feeder मा बनाएँ र fault को स्थान र प्रकारका 39 वटा संयोजन जाँचें। DG नहुँदा 39 मध्ये 39 मा coordination कायम रहन्छ। DG जोडेर साधारण setting राख्दा 24 मा मात्र। DSDR र ठूला fuse राख्दा 39 मध्ये 38 मा।",
    "इमानदार निष्कर्ष: dual setting आवश्यक छ तर एक्लै पर्याप्त छैन। यसलाई fuse को आकार पनि बदल्नुपर्छ, र एउटा अवस्था अझै बिग्रिएकै रहन्छ, किनभने relay को dial त्योभन्दा बढाउन मिल्दैन।",
]

TERMS = [
    ("Recloser", "A breaker with a relay that trips, waits, and closes again by itself.", "आफैँ trip गर्ने, केही समय पर्खने र फेरि आफैँ बन्द हुने breaker।"),
    ("Fuse", "A wire that melts when too much current flows; it must be replaced by hand.", "धेरै current बग्दा पग्लने तार; पग्लिएपछि मान्छेले नै बदल्नुपर्छ।"),
    ("Fuse saving", "Letting the recloser clear a temporary fault before the fuse melts.", "Fuse पग्लनुअघि नै recloser ले अस्थायी fault हटाउने तरिका।"),
    ("DG", "Distributed generator: a generator connected inside the distribution feeder.", "Distribution feeder भित्रै जोडिएको generator।"),
    ("Coordination", "The devices operate in the right order.", "उपकरणहरूले सही क्रममा काम गर्नु; तालमेल।"),
    ("CTI", "Coordination time interval = fuse melting time minus recloser fast time. Must be positive.", "Fuse पग्लने समय र recloser को छिटो trip समयको फरक। यो धनात्मक हुनुपर्छ।"),
    ("Pickup current", "The current above which the relay starts to operate.", "जति current नाघेपछि relay ले काम सुरु गर्छ, त्यो मान।"),
    ("Time dial (TDS, TMS)", "A setting that makes the whole relay curve slower or faster.", "Relay को पूरै curve लाई ढिलो वा छिटो बनाउने setting।"),
    ("Fast and delayed curve", "The recloser's two curves: fast for temporary faults, delayed for permanent ones.", "Recloser का दुई curve: अस्थायी fault का लागि छिटो, स्थायी fault का लागि ढिलो।"),
    ("MMT and TCT", "Minimum melting time and total clearing time of a fuse.", "Fuse पग्लन सुरु हुने न्यूनतम समय र fault पूरै हटाउन लाग्ने कुल समय।"),
    ("Cell", "One fault location with one fault type. There are 39.", "एउटा स्थान र एउटा प्रकारको fault को जोडी। जम्मा 39 वटा छन्।"),
    ("Forward and reverse", "Current from the grid side, and current from the DG side.", "Grid तिरबाट आउने current र DG तिरबाट आउने current।"),
    ("EMT", "A simulation that follows the current wave in time.", "Current को तरङ्गलाई समयसँगै पछ्याउने simulation।"),
    ("Penetration", "How large the DG is, as a percentage of its full size.", "DG कति ठूलो छ भन्ने, पूरा क्षमताको प्रतिशतमा।"),
]

# (slide number, title, say, understand (English), Nepali, optional (question, answer))
SLIDES = [
    (1, "Title",
     "Good afternoon, respected teachers and friends. I am Jhala Nath Kafle, roll number 081 MSPSE 009. My project is on dual-setting directional recloser and fuse coordination in distribution networks with distributed generation.",
     "The title names three things: the device (a recloser with two settings chosen by the direction of the current), what it must work with (the fuses), and the situation (a feeder with a generator connected). In one line: how to keep the recloser and the fuses working in the right order after a generator is added.",
     "शीर्षकले तीन कुरा भन्छ: उपकरण (current को दिशाअनुसार छानिने दुई setting भएको recloser), जोसँग मिलेर काम गर्नुपर्छ (fuse), र अवस्था (generator जोडिएको feeder)। एक वाक्यमा: generator थपेपछि पनि recloser र fuse ले सही क्रममा काम गरिरहने कसरी बनाउने।",
     None),
    (2, "Abstract",
     "A DG can break recloser-fuse coordination. I implemented a dual-setting directional recloser on the IEEE 13-node feeder. With the DG, coordination holds in 24 of 39 cells. With the DSDR and revised fuses, it holds in 38 of 39.",
     "This slide is the whole project in four lines: the problem, the method, the tools, and the result. The two numbers to remember are 24 and 38. The yellow box is the message you want the examiners to keep: the dual setting works, but only together with larger fuses.",
     "यो slide मा पूरै project चार पङ्क्तिमा छ: समस्या, विधि, प्रयोग गरिएका साधन र नतिजा। सम्झनुपर्ने दुई सङ्ख्या 24 र 38 हुन्। पहेँलो बाकसमा भएको कुरा नै परीक्षकले सम्झून् भन्ने मुख्य सन्देश हो: dual setting ले काम गर्छ, तर fuse को आकार बढाएपछि मात्र।",
     ("What is a cell?", "One fault location with one fault type. Twelve locations and four fault types give 39 cells, because not every node has all three phases.")),
    (3, "Presentation Roadmap",
     "I will go through the introduction, the literature, the methodology, the results and the conclusion.",
     "Just the order of the talk. Say it in one breath and move on.",
     "प्रस्तुतिको क्रम मात्र हो। एकै सासमा भनेर अगाडि बढ्नुहोस्।",
     None),
    (4, "Chapter I: Background and Problem",
     "The recloser trips fast to save the fuse on a temporary fault. That works only while both carry the same current. With a DG, the fuse carries more current than the recloser, and it can melt first.",
     "Look at the graph. The solid blue line is the recloser's fast curve, the green band is the fuse, and the dashed line is the recloser's delayed curve. For fuse saving the fast curve must be below the fuse and the delayed curve above it. This is true only between points A and B. A DG pushes the fuse current to the right, outside that range, while the recloser current stays where it was.",
     "ग्राफ हेर्नुहोस्। निलो सिधा रेखा recloser को छिटो curve हो, हरियो पट्टी fuse हो, र थोप्ले रेखा recloser को ढिलो curve हो। Fuse saving का लागि छिटो curve fuse भन्दा तल र ढिलो curve fuse भन्दा माथि हुनुपर्छ। यो A र B बिन्दुको बीचमा मात्र सत्य हुन्छ। DG ले fuse को current लाई दायाँतिर, त्यो दायराभन्दा बाहिर धकेल्छ, तर recloser को current भने जहाँको त्यहीँ रहन्छ।",
     ("Why does the recloser not see the DG current?", "The DG is connected beyond the recloser, closer to the fault. Its current goes straight into the fault through the fuse and never passes the recloser.")),
    (5, "Chapter I: Objectives and Study Scope",
     "The general objective is to build and validate the DSDR method on the IEEE 13-node feeder in PowerFactory. There are seven specific objectives, from building the model to the DG penetration study.",
     "The general objective is the one big aim. The seven specific objectives are the steps taken to reach it, in the order the work was done: build the model, run the studies, calculate the settings, check without DG and with DG, apply the dual setting, verify in time, and vary the DG size. Do not read all seven aloud.",
     "General objective भनेको एउटा मुख्य लक्ष्य हो। सात वटा specific objective त्यो लक्ष्यमा पुग्न चालिएका कदम हुन्, काम गरिएकै क्रममा: model बनाउने, अध्ययन चलाउने, setting निकाल्ने, DG बिना र DG सहित जाँच्ने, dual setting लगाउने, समयमा प्रमाणित गर्ने, र DG को आकार फेरेर हेर्ने। सातै वटा ठूलो स्वरमा नपढ्नुहोस्।",
     None),
    (6, "Chapter II: Literature Positioning and Gap",
     "The literature covers coordination with DG, the DSDR method, relay curves and the test feeder. The gap is an independent implementation with real relay curves, dial ranges and fuse sizes.",
     "Each row is a group of earlier work and what it leaves open. The key row is the second: the DSDR method comes from the reference paper, but that paper does not give all the settings and fuse sizes. The gap this project fills is to build the method independently, with the curves and limits of real devices.",
     "हरेक पङ्क्तिमा पहिलेका कामको एउटा समूह र त्यसले बाँकी छोडेको कुरा छ। मुख्य पङ्क्ति दोस्रो हो: DSDR विधि reference paper बाट आएको हो, तर त्यो paper मा सबै setting र fuse को आकार दिइएको छैन। यो project ले पूरा गर्ने खाली ठाउँ भनेको वास्तविक उपकरणका curve र सीमासहित यो विधिलाई स्वतन्त्र रूपमा बनाउनु हो।",
     ("Is your work only a copy of the paper?", "No. It is an independent implementation. I used the manufacturers' curves and real dial ranges, validated the model against the IEEE benchmark, and found where the method reaches the limits of the devices.")),
    (7, "Chapter III: Study System and Inputs",
     "This is a 4.16 kV feeder with a 4.05 MVA synchronous DG at node 692. R1 is at the feeder head, R2 is on line 632 to 671, and fuses protect the laterals.",
     "The diagram shows where everything is. Power comes in at the top. R1 sits at the head of the feeder and sees every fault. R2 sits in the middle. The DG is at node 692, below R2. So for a fault above R2, the DG current flows backwards through R2. That is the reason R2 needs a reverse setting. The lower table gives the generator's data.",
     "चित्रले कुन चिज कहाँ छ भनेर देखाउँछ। बिजुली माथिबाट आउँछ। R1 feeder को सुरुमा छ र हरेक fault देख्छ। R2 बीचमा छ। DG node 692 मा, R2 भन्दा तल छ। त्यसैले R2 भन्दा माथिको fault मा DG को current R2 बाट उल्टो दिशामा बग्छ। R2 लाई reverse setting चाहिनुको कारण यही हो। तलको तालिकामा generator का विवरण छन्।",
     ("Why node 692 for the DG?", "It is the location used in the reference method. It is downstream of R2, so it creates reverse current in R2 for faults upstream.")),
    (8, "Chapter III: Overall Methodology Flowchart",
     "A load flow gives the branch currents, and each recloser's pickup is set at 1.25 times that current. R2 gets separate forward and reverse settings, for the grid and the DG. The fuses are sized, and then every fault is checked. If coordination fails, the time dial is adjusted first, and the fuse is made larger if necessary.",
     "Read the flowchart from top to bottom. First find the normal current in each branch. The relay must not trip on normal current, so its pickup is set 25 per cent higher. For R2 this is done twice, once for each direction. Then test every fault. If the fuse would melt before the recloser trips, try to fix it with the dial. If the dial is already at its end, use a larger fuse and test again.",
     "Flowchart लाई माथिबाट तल पढ्नुहोस्। पहिले हरेक शाखामा सामान्य अवस्थाको current निकालिन्छ। Relay ले सामान्य current मा trip गर्नु हुँदैन, त्यसैले pickup लाई 25 प्रतिशत बढी राखिन्छ। R2 का लागि यो दुई पटक गरिन्छ, हरेक दिशाका लागि एक-एक पटक। त्यसपछि हरेक fault जाँचिन्छ। Recloser ले trip गर्नुअघि नै fuse पग्लने देखिए पहिले dial मिलाएर सुधार्ने प्रयास गरिन्छ। Dial पहिले नै अन्तिम सीमामा छ भने ठूलो fuse राखेर फेरि जाँचिन्छ।",
     ("Why 1.25?", "It is the overload factor of the method. It keeps the relay from tripping on normal load, with a 25 per cent allowance.")),
    (9, "Chapter III: Mathematical Formulation of the Method",
     "These are the method's equations: the recloser curve, the pickup, the fuse line and the coordination conditions.",
     "Four boxes. Box 1: the time a recloser takes depends on how many times the fault current is above the pickup; a bigger current gives a shorter time. Box 2: the pickup is 1.25 times the rated current. Box 3: the fuse curve is a straight line on log-log paper. Box 4: the two conditions that mean coordination holds. Point at box 4 if time is short.",
     "चार वटा बाकस छन्। बाकस 1: recloser लाई लाग्ने समय fault current pickup भन्दा कति गुणा बढी छ भन्नेमा भर पर्छ; current जति ठूलो, समय त्यति छोटो। बाकस 2: pickup भनेको rated current को 1.25 गुणा हो। बाकस 3: log-log कागजमा fuse को curve सिधा रेखा हुन्छ। बाकस 4: coordination कायम छ भन्ने जनाउने दुई सर्त। समय कम भए बाकस 4 मात्र देखाउनुहोस्।",
     ("What does CTI greater than zero mean?", "The fuse starts to melt later than the recloser's fast trip. So the recloser acts first and the fuse is saved.")),
    (10, "Chapter III: Formulation Used for the Operating Times",
     "I kept the method's structure and used each manufacturer's curve: the GE IAC equation for R1 and the CDG34 table for R2. R1 reproduces the paper's worked example.",
     "The method's formula has constants A, B and n that describe a general curve. A real relay has its own fixed curve from its manufacturer. So the form 'time = dial times a function of current' is kept, and the function is taken from the real device. The proof that this is right: for 4219 amperes R1 gives 0.096 seconds, and the paper gives 0.097.",
     "विधिको सूत्रमा A, B र n भन्ने स्थिराङ्क छन्, जसले एउटा सामान्य curve जनाउँछन्। वास्तविक relay को भने निर्माताले दिएको आफ्नै निश्चित curve हुन्छ। त्यसैले 'समय = dial गुणा current को function' भन्ने ढाँचा जस्ताको तस्तै राखिएको छ, र function चाहिँ वास्तविक उपकरणबाट लिइएको छ। यो ठीक छ भन्ने प्रमाण: 4219 ampere मा R1 ले 0.096 सेकेन्ड दिन्छ, र paper मा 0.097 छ।",
     ("Why did you change the paper's formula?", "I did not change the method. I replaced the generic curve with the curve of the actual relay, because a real relay cannot follow arbitrary constants. The pickups, dials and coordination rules are the method's.")),
    (11, "Chapter III: Protection Settings",
     "R1 picks up at 720 amperes. R2 has a forward group of 300 and 600 amperes, and a new reverse group of 150 and 300. The dials were already at their limits, so the fuses were revised.",
     "The table is the result of the design. R2 has two rows: forward for grid current, reverse for DG current. The reverse values are smaller because the DG is a smaller source than the grid. The first bullet is the key fact: without DG, 470 amperes flow one way through R2; with DG, 252 amperes flow the other way.",
     "यो तालिका design को नतिजा हो। R2 का दुई पङ्क्ति छन्: grid को current का लागि forward र DG को current का लागि reverse। Reverse का मान साना छन्, किनभने DG grid भन्दा सानो स्रोत हो। पहिलो बुँदा नै मुख्य तथ्य हो: DG नहुँदा R2 बाट 470 ampere एक दिशामा बग्छ; DG हुँदा 252 ampere अर्को दिशामा बग्छ।",
     ("Why is R1's dial called TDS and R2's called TMS?", "They are the two manufacturers' names for the same thing: the setting that scales the curve.")),
    (12, "Chapter IV: Base Case Without DG",
     "Without DG, 35 of 39 cells are coordinated, and all 39 after one fuse change.",
     "This is the starting point: the feeder works properly before the DG is added. The plot shows one fault. R2 trips at 0.128 seconds and the fuse would melt at 0.271 seconds, so the recloser is first. The four cells lost at the start were a fuse-to-fuse problem, fixed by changing one fuse size.",
     "यो सुरुको अवस्था हो: DG थप्नुअघि feeder ले राम्ररी काम गर्छ। ग्राफले एउटा fault देखाउँछ। R2 ले 0.128 सेकेन्डमा trip गर्छ र fuse 0.271 सेकेन्डमा मात्र पग्लन्थ्यो, त्यसैले recloser अगाडि छ। सुरुमा बिग्रिएका चार cell दुई fuse बीचको समस्या थिए, एउटा fuse को आकार बदलेर सुधारियो।",
     None),
    (13, "Chapter IV: Branch Currents and Fault Levels - Side by Side",
     "Rated currents agree with the paper within 2 per cent. My fault levels match the IEEE benchmark within 2 per cent; the paper's fault levels are higher.",
     "Three sources are compared: my study, the reference paper, and the IEEE benchmark. Load currents match the paper. Fault currents do not: mine are lower. To find out which is right, I compared both with the IEEE benchmark. Mine are within 2 per cent of it (green column). The paper's are much higher (red column). This is why some of my results differ from the paper.",
     "तीन स्रोतको तुलना गरिएको छ: मेरो अध्ययन, reference paper र IEEE benchmark। Load current paper सँग मिल्छ। Fault current भने मिल्दैन: मेरो कम छ। कुन सही हो भनेर थाहा पाउन मैले दुवैलाई IEEE benchmark सँग दाँजें। मेरो मान benchmark को 2 प्रतिशतभित्र छ (हरियो स्तम्भ)। Paper का मान धेरै बढी छन् (रातो स्तम्भ)। मेरा केही नतिजा paper भन्दा फरक हुनुको कारण यही हो।",
     ("Why are your fault levels lower than the paper's?", "My model includes the substation transformer and matches the IEEE short-circuit benchmark within 2 per cent. Two of the paper's values are even higher than its own value at the feeder head, which is not possible in a radial feeder without DG.")),
    (14, "Chapter IV: Fuse Coefficients - Side by Side",
     "The fuse coefficients agree with the paper's Table three within 0.33.",
     "The coefficient b fixes where each fuse's line sits on the graph. The two columns, mine and the paper's, are close for all 15 fuses. Small differences come from the lower fault currents. One sentence is enough here.",
     "गुणाङ्क b ले हरेक fuse को रेखा ग्राफमा कहाँ बस्छ भन्ने तोक्छ। मेरो र paper को, दुवै स्तम्भ 15 वटै fuse मा नजिक छन्। सानो फरक कम fault current का कारण आएको हो। यहाँ एक वाक्य नै पुग्छ।",
     None),
    (15, "Chapter IV: DG Connected, Conventional R2",
     "With the DG and the same settings, only 24 of 39 cells hold coordination. The fuse melts before the fast trip.",
     "Now the DG is switched on and nothing else is changed. Green ticks are cells that still work; red crosses are cells where the fuse melts first. Fifteen cells are lost. They are near the DG and upstream of R2: nodes 633, 645, 646, the distributed load, and 675.",
     "अब DG चालु गरिन्छ र अरू केही बदलिँदैन। हरियो चिह्न भएका cell अझै ठीक छन्; रातो क्रस भएका cell मा fuse पहिले पग्लन्छ। पन्ध्र वटा cell बिग्रन्छन्। ती DG नजिक र R2 भन्दा माथि छन्: node 633, 645, 646, distributed load र 675।",
     ("Why exactly does it fail?", "Two reasons. The fuse carries grid plus DG current, so it melts sooner. And R2 sees only the reverse DG current, which is small, so with its forward setting it is slow or does not pick up at all.")),
    (16, "Chapter IV: Coordination with DG - Side by Side",
     "I hold coordination in 24 cells, and the paper in 30. We agree in 29 of the 39 cells.",
     "The same result, cell by cell, next to the paper's. Top grid is mine, bottom is the paper's. In 29 cells we give the same answer. In 8 cells I lose coordination and the paper holds it; in 2 it is the other way round. The biggest difference is the distributed-load node.",
     "उही नतिजा, cell-cell गरेर, paper को नतिजासँगै राखिएको छ। माथिको जाली मेरो, तलको paper को हो। 29 वटा cell मा हामी दुवैको उत्तर एउटै छ। 8 वटा cell मा मेरोमा coordination बिग्रन्छ तर paper मा कायम रहन्छ; 2 वटामा यसको उल्टो छ। सबैभन्दा ठूलो फरक distributed load को node मा छ।",
     ("Why do you lose more cells than the paper?", "My fault levels follow the IEEE benchmark, and the paper does not publish R2's settings or all fuse sizes. With the same method but different currents and fuses, the cell-by-cell result cannot be identical.")),
    (17, "Chapter IV: Effect of the DG Penetration Level - Side by Side",
     "As the DG grows from 0 to 100 per cent, the CTI falls: at node 633 from plus 4 to minus 51 milliseconds. The paper shows the same trend. This is why an adaptive setting is needed.",
     "This slide shows the problem growing. The DG size is increased in seven steps and the margin (CTI) is measured each time. A positive CTI means the recloser wins; negative means the fuse melts first. The bigger the DG, the smaller the CTI. So a setting that is right for one DG size is wrong for another: the protection must adapt.",
     "यो slide ले समस्या बढ्दै गएको देखाउँछ। DG को आकार सात चरणमा बढाइन्छ र हरेक पटक margin (CTI) नापिन्छ। CTI धनात्मक हुनु भनेको recloser ले जित्नु हो; ऋणात्मक हुनु भनेको fuse पहिले पग्लनु हो। DG जति ठूलो, CTI त्यति सानो। त्यसैले एउटा आकारको DG का लागि ठीक भएको setting अर्को आकारका लागि गलत हुन्छ: सुरक्षा प्रणालीले आफूलाई अवस्थाअनुसार ढाल्नुपर्छ।",
     ("Why does the CTI fall?", "The fuse current rises with the DG, so the fuse melts faster. The recloser's current does not rise; it even falls a little. So the gap between them shrinks.")),
    (18, "Chapter IV: With the DSDR",
     "With the DSDR and revised fuses, 38 of 39 cells hold coordination. The dual setting alone restores seven cells. Only the LG fault at 692 stays lost, at R2's dial limit.",
     "The main result. Only one red cross is left. The small table separates the two improvements: the dual setting alone gives 25, larger fuses alone give 31, and both together give 38. So neither is enough on its own. The remaining case cannot be fixed because R2's delayed dial is already at its maximum.",
     "यो मुख्य नतिजा हो। एउटा मात्र रातो क्रस बाँकी छ। सानो तालिकाले दुई सुधारलाई छुट्ट्याएर देखाउँछ: dual setting एक्लैले 25, ठूला fuse एक्लैले 31, र दुवै सँगै हुँदा 38। त्यसैले कुनै एउटा मात्र पर्याप्त छैन। बाँकी एउटा अवस्था सुधार्न सकिँदैन, किनभने R2 को ढिलो dial पहिले नै अधिकतम मानमा छ।",
     ("Then is the improvement from the DSDR or from the fuses?", "From both. With the revised fuses, a single setting gives 31 and the dual setting gives 38, so seven cells need the dual setting. With the old fuses the dual setting gives only 25. I call it necessary but not sufficient.")),
    (19, "Chapter IV: TCC with the DSDR - Bolted LL Fault at 646",
     "For a line-to-line fault at 646, R2 trips in 0.086 seconds on its reverse group, and R1 in 0.189. The fuse would melt at 0.415, so it is saved.",
     "One fault, drawn on the time-current graph. The fuse carries 3672 amperes, the grid and DG together. R2 sees only the DG part, 1114 amperes backwards, and trips first. R1 sees the grid part and trips second. Both are earlier than 0.415 seconds, when the fuse would begin to melt. The margin is 226 milliseconds.",
     "एउटा fault लाई time-current ग्राफमा देखाइएको छ। Fuse मा 3672 ampere बग्छ, grid र DG दुवैको जोड। R2 ले DG को भाग मात्र, 1114 ampere उल्टो दिशामा देख्छ र पहिले trip गर्छ। R1 ले grid को भाग देख्छ र दोस्रोमा trip गर्छ। दुवै 0.415 सेकेन्डभन्दा अगाडि हुन्छन्, जुन बेला fuse पग्लन सुरु हुन्थ्यो। Margin 226 मिलिसेकेन्ड छ।",
     ("Why must both reclosers trip?", "The fault is fed from two sides. R2 cuts off the DG side and R1 cuts off the grid side. Only when both have opened does the current through the fuse stop.")),
    (20, "Chapter IV: Operating Times with the DSDR - Side by Side",
     "These are my operating times next to the paper's Table four. In both, the fuse melts after the fast trip in every row.",
     "Left is my table, right is the paper's. Do not read the numbers. The point is the pattern: in every row of both tables, the fuse time is longer than the fast trip time. Also, R1's delayed time is exactly 20 times its fast time in both, which confirms the dials 0.5 and 10.",
     "बायाँ मेरो तालिका, दायाँ paper को। सङ्ख्या नपढ्नुहोस्। मुख्य कुरा ढाँचा हो: दुवै तालिकाको हरेक पङ्क्तिमा fuse को समय छिटो trip को समयभन्दा लामो छ। साथै दुवैमा R1 को ढिलो समय छिटो समयको ठ्याक्कै 20 गुणा छ, जसले dial 0.5 र 10 हो भन्ने पुष्टि गर्छ।",
     ("Your times differ from the paper's. Why?", "The operating time depends on the fault current. My fault currents follow the IEEE benchmark and are lower, so R1 is slower in most rows. R2's settings are not published in the paper, so those can only be compared in trend.")),
    (21, "Chapter IV: Single versus Dual Setting",
     "Same fault, same current. With the single setting, R2 trips in 0.121 seconds: coordination is lost. With the reverse group, 0.052 seconds: coordination is held.",
     "The clearest proof that the dual setting matters. Everything is the same in both columns: the fault, the current, the fuse. Only R2's setting group is different. With the forward group R2 is too slow for this small reverse current. With the reverse group, which has a lower pickup, it is fast enough.",
     "Dual setting महत्त्वपूर्ण छ भन्ने सबैभन्दा प्रस्ट प्रमाण यही हो। दुवै स्तम्भमा सबै कुरा उही छ: fault, current र fuse। फरक केवल R2 को setting समूह हो। Forward समूहमा R2 यो सानो reverse current का लागि धेरै ढिलो हुन्छ। कम pickup भएको reverse समूहमा भने पर्याप्त छिटो हुन्छ।",
     ("Why is the reverse group faster for the same current?", "Its pickup is lower: 150 amperes against 300. The same 1777 amperes is a larger multiple of the pickup, and a larger multiple gives a shorter time on an inverse curve.")),
    (22, "Chapter IV: Time-Domain (EMT) Verification",
     "The EMT run confirms it in time. Without DG the fuse survives the two fast shots at 45 per cent of its heat. With DG it melts during the second shot.",
     "This is a simulation of the actual current wave. The recloser trips, waits, recloses, and trips again: two fast shots. A fuse melts when it has collected enough heat. Without DG the two shots use 45 per cent of that heat, so the fuse survives. With DG the fuse current is higher, and the DG keeps feeding the fault even while R2 is open, so the fuse reaches 100 per cent at 0.75 seconds.",
     "यो वास्तविक current को तरङ्गको simulation हो। Recloser ले trip गर्छ, पर्खन्छ, फेरि बन्द हुन्छ र फेरि trip गर्छ: दुई वटा छिटो shot। Fuse ले पर्याप्त ताप जम्मा गरेपछि पग्लन्छ। DG नहुँदा दुई shot ले त्यो तापको 45 प्रतिशत मात्र प्रयोग गर्छन्, त्यसैले fuse बच्छ। DG हुँदा fuse को current बढी हुन्छ, र R2 खुला हुँदा पनि DG ले fault लाई current दिइरहन्छ, त्यसैले fuse 0.75 सेकेन्डमा 100 प्रतिशत पुग्छ।",
     ("Why is the EMT run done with conventional settings?", "The fault at 684 is downstream of R2, where R2 uses its forward group in both schemes. The run shows the cause of the problem in time; it also shows the limit of the method for faults below R2.")),
    (23, "Chapter IV: Summary and Comparison",
     "In summary, coordination holds in 24 cells with a conventional recloser, 25 with the DSDR alone, 31 with the fuse revision alone, and 38 with both. The paper reports 30 and 39.",
     "All the counts in one table. Read down the middle column: 35, 39, 24, 25, 31, 38. The right column gives the paper's two published counts, 30 and 39. The trend is the same in both: the DG reduces coordination, and the DSDR with the fuse revision restores it.",
     "सबै गन्ती एउटै तालिकामा छन्। बीचको स्तम्भ माथिबाट तल पढ्नुहोस्: 35, 39, 24, 25, 31, 38। दायाँको स्तम्भमा paper मा प्रकाशित दुई गन्ती, 30 र 39 छन्। दुवैमा प्रवृत्ति उही छ: DG ले coordination घटाउँछ, र DSDR सँगै fuse को परिवर्तनले त्यसलाई फेरि कायम गराउँछ।",
     ("The paper gets 39 and you get 38. Is your result worse?", "It is one cell, the LG fault at 692. There the fuse must be large to stay selective with the fuse below it, and then it clears after R2's delayed trip. R2's delayed dial is already at its maximum, so a real CDG34 relay cannot do better.")),
    (24, "Chapter V: Conclusion and Future Scope",
     "To conclude: the DSDR with the fuse revision raises coordination from 24 to 38 of 39 cells. It is necessary but not sufficient, because it needs the fuse revision. Future work includes the 34-node feeder, a true directional element and inverter-based DG.",
     "The conclusion repeats the story in five lines: the model is valid, it works without DG, the DG breaks it, the DSDR with larger fuses repairs it, and there is a limit. The future work lists what was not done: a larger feeder, a relay model that senses direction itself, and DG connected through inverters, which behaves differently in a fault.",
     "निष्कर्षले पूरै कथालाई पाँच पङ्क्तिमा दोहोर्‍याउँछ: model ठीक छ, DG बिना यसले काम गर्छ, DG ले यसलाई बिगार्छ, DSDR र ठूला fuse ले सुधार्छन्, र एउटा सीमा छ। Future work मा गर्न बाँकी काम छन्: ठूलो feeder, दिशा आफैँ चिन्ने relay को model, र inverter मार्फत जोडिएको DG, जसले fault को बेला फरक व्यवहार गर्छ।",
     ("What is the main limitation of your work?", "The library relay is not directional, so the two groups are modelled as separate relay units and the direction is assigned from the fault location. Also, coordination is judged with a zero margin, and only one DG location is studied.")),
    (25, "References",
     "These are the main references.",
     "Reference 1 is the method. References 5 and 7 are the test feeder and its short-circuit benchmark. Reference 4 is the relay manual for R1's curve.",
     "Reference 1 विधिको स्रोत हो। Reference 5 र 7 test feeder र त्यसको short-circuit benchmark हुन्। Reference 4 R1 को curve का लागि प्रयोग गरिएको relay को manual हो।",
     None),
    (26, "Thank You",
     "Thank you. I am happy to take your questions.",
     "Stop here and wait. If you do not understand a question, ask the examiner to repeat it.",
     "यहाँ रोकिनुहोस् र पर्खनुहोस्। प्रश्न नबुझे परीक्षकलाई फेरि भन्न अनुरोध गर्नुहोस्।",
     None),
]

NUMBERS = [
    ("Feeder voltage", "4.16 kV"), ("DG", "4.05 MVA synchronous, at node 692"),
    ("Cells studied", "39 (12 locations, 4 fault types)"),
    ("R1 pickup and dials", "720 A; TDS 0.5 / 10"), ("R2 forward plugs", "300 / 600 A"),
    ("R2 reverse plugs", "150 / 300 A"), ("Current through R2", "470 A without DG; 252 A reversed with DG"),
    ("Reverse pickup", "1.25 x 252 = 315 A"), ("Fault level at feeder head", "4.73 kA"),
    ("No DG", "35 of 39, then 39 of 39"), ("DG, conventional R2", "24 of 39"),
    ("DSDR alone / fuses alone / both", "25 / 31 / 38 of 39"), ("Paper", "30 and 39"),
    ("Cell still lost", "LG fault at 692"), ("CTI at 633, DG 0 to 100 per cent", "+4 ms to -51 ms"),
    ("EMT: fuse heat after two fast shots", "45 per cent without DG; melts at 0.75 s with DG"),
]


def tex(s):
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        s = s.replace(a, b)
    return s


def words(s):
    return len(re.findall(r"[\w.']+", s))


body = []
for n, title, say, und, nep, qa in SLIDES:
    b = ["\\begin{slideblock}{%d}{%s}{c%02d.png}" % (n, tex(title), n),
         "\\lab{Say}{navy}\\saytext{%s}" % tex(say),
         "\\lab{Understand}{teal}\\plain{%s}" % tex(und),
         "\\lab{\\nep नेपालीमा}{maroon}\\neptext{%s}" % tex(nep)]
    if qa:
        b.append("\\lab{If asked}{gray}\\plain{\\textbf{%s} %s}" % (tex(qa[0]), tex(qa[1])))
    b.append("\\end{slideblock}\n")
    body.append("\n".join(b))
total = sum(words(x[2]) for x in SLIDES)

DOC = r"""\documentclass[11pt,a4paper]{article}
\usepackage[left=1.7cm,right=1.7cm,top=1.6cm,bottom=1.8cm]{geometry}
\usepackage{fontspec}
\setmainfont{Times New Roman}
\newfontfamily\nep[Script=Devanagari,Scale=0.93]{Nirmala UI}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{array}
\usepackage{longtable}
\usepackage{colortbl}
\usepackage{needspace}
\usepackage{fancyhdr}
\graphicspath{{slides_ch/}}
\definecolor{navy}{HTML}{0B2545}
\definecolor{teal}{HTML}{1E6F5C}
\definecolor{maroon}{HTML}{8A2B2B}
\definecolor{rule}{HTML}{C9CED6}
\definecolor{headc}{HTML}{E6ECF5}
\definecolor{warm}{HTML}{FFF8E8}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.3}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyfoot[C]{\small\color{gray} Presentation guide --- page \thepage}
\newcommand{\sect}[1]{\needspace{6\baselineskip}\bigskip{\Large\color{navy}\bfseries #1}\par\smallskip{\color{navy}\hrule height 0.8pt}\medskip}
\newenvironment{slideblock}[3]{\par\needspace{8.5cm}\vspace{6pt}{\color{navy}\rule{\linewidth}{1.1pt}}\par\vspace{4pt}
  \noindent\begin{minipage}[c]{0.56\linewidth}{\fontsize{20}{22}\selectfont\bfseries\color{navy} SLIDE #1}\par\vspace{4pt}
  {\large\bfseries #2}\end{minipage}\hfill
  \begin{minipage}[c]{0.42\linewidth}\raggedleft\fcolorbox{rule}{white}{\includegraphics[width=0.95\linewidth]{#3}}\end{minipage}\par\vspace{6pt}}{\par\vspace{4pt}}
\newcommand{\lab}[2]{\par\vspace{7pt}\noindent{\small\bfseries\color{#2} #1}\par\vspace{2pt}}
\newcommand{\saytext}[1]{\noindent\colorbox{headc}{\parbox{\dimexpr\linewidth-2\fboxsep}{\fontsize{12.5}{17}\selectfont\raggedright #1}}\par}
\newcommand{\plain}[1]{\noindent{\fontsize{11}{15}\selectfont #1}\par}
\newcommand{\neptext}[1]{\noindent{\nep\fontsize{11}{18.5}\selectfont #1}\par}

\begin{document}
\begin{center}
{\LARGE\bfseries\color{navy} Presentation Guide}\\[4pt]
{\large Speaker notes and an explanation of every slide, in English and Nepali}\\[3pt]
{\nep\large हरेक slide को speaker note र बुझाइ, अङ्ग्रेजी र नेपालीमा}\\[4pt]
Jhala Nath Kafle (081MSPSE009) \quad --- \quad \textit{DSDR\_Presentation\_Chaptered.pptx}, 26 slides
\end{center}

\noindent\fcolorbox{orange}{warm}{\parbox{\dimexpr\linewidth-2\fboxsep-2\fboxrule}{\textbf{How to use this guide.}
Each slide has four parts. \textbf{Say} is the speaker note: read it aloud, it is the same as in the deck's notes.
\textbf{Understand} explains the slide in plain English, for you, not for reading aloud.
{\nep\textbf{नेपालीमा}} is the same explanation in Nepali. \textbf{If asked} gives a likely question and a short answer.
The speaker notes total WORDS words, about MINUTES minutes at a calm pace.\par\smallskip
{\nep\fontsize{11}{18}\selectfont \textbf{यो guide कसरी प्रयोग गर्ने।} हरेक slide मा चार भाग छन्। \textbf{Say} भनेको बोल्ने कुरा हो: यसलाई
ठूलो स्वरमा पढ्नुहोस्। \textbf{Understand} ले slide लाई सरल अङ्ग्रेजीमा बुझाउँछ; यो तपाईंको बुझाइका लागि हो, पढेर सुनाउनका लागि होइन।
\textbf{नेपालीमा} भागमा त्यही बुझाइ नेपालीमा छ। \textbf{If asked} मा सोधिन सक्ने प्रश्न र छोटो उत्तर छ। प्राविधिक शब्दहरू
(recloser, fuse, DG, CTI) अङ्ग्रेजीमै राखिएका छन्, किनभने defence मा तपाईंले तिनै शब्द प्रयोग गर्नुहुनेछ।}}}

\sect{1. The whole story in one page}
STORYEN

\medskip
{\nep\large\bfseries\color{maroon} पूरा कथा एक पृष्ठमा}\par\medskip
STORYNE

\sect{2. Key terms}
\begin{longtable}{|>{\raggedright\arraybackslash}p{3.3cm}|>{\raggedright\arraybackslash}p{6.4cm}|>{\raggedright\arraybackslash}p{6.4cm}|}\hline
\rowcolor{headc}\textbf{Term} & \textbf{Meaning} & {\nep\textbf{नेपालीमा}} \\ \hline
TERMS
\end{longtable}

\newpage
\sect{3. Slide by slide}
SLIDES

\newpage
\sect{4. Numbers to remember}
\begin{longtable}{|>{\raggedright\arraybackslash}p{7.2cm}|>{\raggedright\arraybackslash}p{9.2cm}|}\hline
\rowcolor{headc}\textbf{Quantity} & \textbf{Value} \\ \hline
NUMBERS
\end{longtable}
\end{document}
"""
story_en = "\n\n".join("\\plain{%s}\\vspace{5pt}" % tex(p) for p in STORY_EN)
story_ne = "\n\n".join("\\neptext{%s}\\vspace{5pt}" % tex(p) for p in STORY_NE)
terms = "\n".join("\\textbf{%s} & %s & {\\nep\\fontsize{10.5}{16}\\selectfont %s} \\\\ \\hline" % (tex(a), tex(b), tex(c)) for a, b, c in TERMS)
numbers = "\n".join("%s & %s \\\\ \\hline" % (tex(a), tex(b)) for a, b in NUMBERS)
doc = (DOC.replace("WORDS", str(total)).replace("MINUTES", "%.0f" % round(total / 125.0))
          .replace("STORYEN", story_en).replace("STORYNE", story_ne).replace("TERMS", terms)
          .replace("SLIDES", "\n".join(body)).replace("NUMBERS", numbers))
open(os.path.join(HERE, "DSDR_Presentation_Guide.tex"), "w", encoding="utf-8").write(doc)
print("speaker notes: %d words, about %.1f minutes" % (total, total / 125.0))
