# Phase 2 baseline capture — 2026-07-24T18:48:05-04:00

> **2026-07-24 addendum:** the drawable/preview hashes below record the
> tree as imported in Phase 1, which the same-day device session proved
> to be WARBIRD-contaminated for 46 of 53 PNGs (+preview) — see
> `../candidate/ASSET_DIVERGENCE_FINDING.md`. They are kept as the honest
> point-in-time record. The corrected tree byte-matches the immutable
> release APK instead. The `watchface.xml` hash (`a8ce33ac…`) was and
> remains correct — now proven byte-identical to the APK's own copy.

main head: a99551fa9b31282a6d404918c380e8e13e678337 (descends from 84145b2: yes)
branch: phase-2/aurelius-reference-engine @ a99551fa9b31282a6d404918c380e8e13e678337

## tools/validate.py

0 error(s), 12 warning(s) — 10 source faces checked, aapt2=yes

## git diff --check
clean

## CI on main
completed  success  docs: define Phase 2 Aurelius reference-engine scope  validate  main  push  30131094086  21s  2026-07-24T22:29:32Z
completed  success  docs: define build-time WFF engine and Aurelius reference  validate  main  push  30130990622  16s  2026-07-24T22:27:26Z

## SHA-256 baseline (immutable references)
844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2  releases/aurelius/current/aurelius.apk
a8ce33ac1614430ed896a72964ce96572c363a000d690a9ef4cacf2a590fd29b  watchfaces/aurelius/app/src/main/res/raw/watchface.xml

### All Aurelius runtime resources (drawable*, font, values, xml)
c01788cd20d19e3a911c05b511d2c660ac7dd9b24328219170e289a3ab5057d9  watchfaces/aurelius/app/src/main/res/drawable-nodpi/balance.png
6272544723916ceef7302444b4eae17d7c2e5590010c233df22cf6690cd803b8  watchfaces/aurelius/app/src/main/res/drawable-nodpi/bg_aod.png
dda14123ead5645aa8ff682c76587af899b45ea223172f32e6fba445d205db9e  watchfaces/aurelius/app/src/main/res/drawable-nodpi/bg.png
b90ef13b8a9f24ef7051a48f2742413774fc20484f0e75241192274aba7501d7  watchfaces/aurelius/app/src/main/res/drawable-nodpi/cage.png
3ee58aa72923d21a8d3bd39c50d2cf58a8223230d23b5034d8f4a9d35a90de67  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_0.png
c33a05551a615180ab19cdf2f4271bf0159c89ab178fc67bf665c23d2b65bf5d  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_1.png
3cebe4bc9565a0b2967377073d885f958b88d672d20eaefc87ea349144f575e1  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_2.png
615404e436b9887f5ec724a0f626af52cc992f397f4069668335f9973b8d9304  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_3.png
802fb30902e662141092a9913964c54d5c3f2d2472d814de1d644db7d97b2497  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_4.png
1753e64ac19a03bae60ddbd25e1325dfdee2de84a7149d7fc567f8ffeedb23e5  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_5.png
da16c3731af9d209f9f6c556bd03798395839e25534a695ccb27c65295a68775  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_6.png
a3f6033e348dc027e99e8e53115138bffd7067e8560a6dd5835b956cf4758671  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_7.png
3b21f6d0e33916c925680a6c04607e66983e585157ac2d1178f7ddac11cc13f2  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_8.png
3ba8f9cdc472aba401d4345b72afaf890155526525f79a0af106b491cfd4f8ee  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_9.png
7ceef1ee2462100b714208d07f577232c2a20ce43bf58cecb9456d9efc864fd6  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_a.png
badff71bbfa663699c1598939e56e00f711707a655ecff69d72db33a7cb6cf9c  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_b.png
a0d0e7010d85d5d98eca03dff1450b8d25733b569b0b1ab330f5c62b6674272e  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_colon.png
e2bb56d92cab89ee41f7bdea406d1483e9b4de1d0ac95984d4681821b6c4950e  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_c.png
777299978a13e591eca9f580e3a24c5138cb2f8ea538d9dd141fec06aa7ca2d9  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_d.png
a818fbf31c9a0bdf605dec62815b2824cf7226d2a0f3379c3f75be10d7b421ea  watchfaces/aurelius/app/src/main/res/drawable-nodpi/gear_l.png
88a36055bc88af2e77e4e43693fac8040e7366de88d92bd70e25287410843e65  watchfaces/aurelius/app/src/main/res/drawable-nodpi/gear_r.png
dc20226d342919ddd3d59949d5d8b11ffda0382221b15e9e6d4b47de5630faff  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_e.png
a4827d5c26e5c04dc2e650a213d9b3104858fd216ac982ffca562c35072791ee  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_f.png
edbdb95dddaaf4e7fdf304e28e85c62121e9b0919ef4810b4b20cd956d9a97a2  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_g.png
10b0c743c539490aaf8ac853c4734492aededb3884ea2012c20625a1d788a150  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_h.png
6faa7a04f857efbaab26f3cd1c3571bf3c2b5c6a565214d0a796258fb54ee84d  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_i.png
16354939afdb710e477eff5cddfac15022d21d5b88ac1b334378eb55f9780d05  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_j.png
3ae3f58b9c239b6b7067b660c69c2da1623aa72e5fed4887a31b8eb3d1658066  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_k.png
5cf55673d8f775b75ac2c6148b92a792959961a230d3f7b8ecd834799d5adaae  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_l.png
c504a3b090ea2b8f4d0541706ebf2cc628b4c05a68bea41dacc535badefe169c  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_m.png
d98eb38bda7483fc5f18856f1fbb4bc9b8683542019baf9c0a6b2e7089ae6b95  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_n.png
3a96de13d7c71fca88bd19235056315272068a7e280175c96f3a023d5164850f  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_o.png
976f13525288d9e8efacb089e6cef6669481c7e87eb4b0b56d345ccda59ce2c2  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_pct.png
d257df8368afda99ca326c1da4dfbf131fb168832bafc74f605f0c77ae5f78e5  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_p.png
7156b518f8f226ab384f331097a1d6f242b75918d7197c2b768e6452f4dba075  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_q.png
734649de7c1c3cbf267551a3bca36082095cfb6f4ad43cbff6ad71d9a356dca3  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_r.png
7788e8d6562575fab34cbc0c65a2a2c3cfe7451012fc233e0b9d2de44b1fe369  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_space.png
8176b2346083d284888d8b20e7b6270feb1c3663a5b6b11df28fc38d59bdb01b  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_s.png
bf39d65b03ca8cb565848fac4ee4f31d48ebe1956cba618fc3b0e6c72677c8cf  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_t.png
d03cab566f3ceb68afa031c49257bd613a399e4efb24f8576360a1824dd81005  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_u.png
c89392f96ef7403ed176156eae7c050cdca494eef3353d25f212835d937247c7  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_v.png
9a9f2e78206ab0ec076d48c125ae8cc5ca0f49f0bf7e0aadb7807236a8dbcb39  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_w.png
672569c917088b31a15ccd6f11091b15d2da61afb43a1dd19d7220ba92dd415c  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_x.png
30b93a4d9759e0375106a7ab67c766847301b51b595bbf32595689ba4c93acde  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_y.png
05cfaf0e1b688d8a6f67d954b17be4d6998f7d9a3ed517e8f1a3ff57e08cf6e0  watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_z.png
b3982d478e89ef6aca7aa9b2b3b107ba542ba673ee2d6cef5c24af8e293cc80e  watchfaces/aurelius/app/src/main/res/drawable-nodpi/hour_hand.png
632b9e2170c10838b9237a4d0db134b04cd8fda4a22083147b22ba19896b6868  watchfaces/aurelius/app/src/main/res/drawable-nodpi/hub.png
4e4f3fd2b3ee1e675e7f863eab9e2e74ced51f7bc15ec89a1c77d39fe4e76c9d  watchfaces/aurelius/app/src/main/res/drawable-nodpi/min_hand.png
32305ef1a97a1bb0b7b4778c8fd50556c7ce9e2e2aa985600a4fd0ba68a386f4  watchfaces/aurelius/app/src/main/res/drawable-nodpi/needle.png
01aaae47f34b3340be4d6cf095f90411243bea316002e644499750e6a5d8edf7  watchfaces/aurelius/app/src/main/res/drawable-nodpi/prop.png
b9154465e2b6a0b1079abf687c15909ef2d49f4f7c62435d57d84d07279c5fa4  watchfaces/aurelius/app/src/main/res/drawable-nodpi/resv_needle.png
359d05233215d2516575f9d84ed6cc70638281ee3c6912b426971a430618667d  watchfaces/aurelius/app/src/main/res/drawable-nodpi/sheen.png
c12c70c322bb32999eadff23ca3b6f45bc43df73aeae0ad4ce56ce9cd68bd95f  watchfaces/aurelius/app/src/main/res/drawable-nodpi/tourb_base.png
fe84f7f1ec4efb93b86d334230507efd2c5352f8b8e7f75d06769588a5fe03e9  watchfaces/aurelius/app/src/main/res/drawable-nodpi/tourb_disc.png
1f42a033a7ec2f5c533ef7a0bac94b79b5359a00487cf8dd22814adeba5079f0  watchfaces/aurelius/app/src/main/res/drawable-nodpi/tourb_rim.png
7252e0b9c85ea75f231ca7428ce2c60350827a9bb959f69ef71d7df95d2990b5  watchfaces/aurelius/app/src/main/res/drawable/preview.png
03044ab65228b0554c9a5c1e63df29d4e58a71857e212801aaf768dfd106bdf0  watchfaces/aurelius/app/src/main/res/font/marcellus_sc.ttf
1cf0cd10b17d35e852729962cc1ffaffed94514895972458345e2df34abb2f81  watchfaces/aurelius/app/src/main/res/font/marcellus.ttf
691470dd3286a14e9677940d0bf75796179841ba5215cbda1a2c8910a3226afd  watchfaces/aurelius/app/src/main/res/font/rajdhani_bold.ttf
a8ce33ac1614430ed896a72964ce96572c363a000d690a9ef4cacf2a590fd29b  watchfaces/aurelius/app/src/main/res/raw/watchface.xml
8f2b6bc3f8e17519814f139c51ebe831071e045635e5846221e09bfeb9d27fab  watchfaces/aurelius/app/src/main/res/values/integers.xml
885e2dc93bba9638e025c4b57bcdb2f7cdea128db1c7c05a0b9ba0046ccf5136  watchfaces/aurelius/app/src/main/res/xml/watch_face_info.xml
