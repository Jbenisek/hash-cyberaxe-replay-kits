"""Generic collision search on the Orchard hash with 56 partial rounds, the permutation evaluated in an equivalent form whose every
field operation is charged: one trail of x -> F(x) = digest(message(kappa x - E0_0)) / OUTSCALE_kappa for a random coin kappa, distinguished
points, one bit-packed table (142-bit value, 119-bit index gap per entry), single-gap recovery.

Target: poseidon-orchard-r56-prefix-v1 (initial state [m0, m1, 2^65], 8 full + 56 partial rounds, digest = state[0], no feed-forward).
Sections: 1 deployed constants (halo2_poseidon 0.2.0, copied from our own checked file), 2 the hash (reference form), 3 the input line and the
step program (`line`, `build_step`), 4 the search (`search`), 5 parameters and ledger (`plan`, `python3 rho.py --plan`; `--tune` re-derives
the parameter literals and counts the offline work at the prices of the word machine `Wm`), 6 self-checks (`--selftest`) and command line
(`--listing` prints the step program).
No outside code or library is used; standard library only.
"""
import sys
import json
import hashlib
from math import log2
from fractions import Fraction

PARTIAL = 56
LEV = "BCD"                               # the variant of this program (fixed): B whole-value DP test (compare + branch), C down-counter block, D multiplicative coin
LEV_B, LEV_C, LEV_D, LEV_1 = "B" in LEV, "C" in LEV, "D" in LEV, "1" in LEV
assert not LEV_1 or LEV_B
# ================================================================ 1 constants
P = 0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001
ROUND_CONSTANTS = (
    (0x360d7470611e473d353f628f76d110f34e71162f31003b7057538c2596426303, 0x2bab94d7ae222d135dc3c6c5febfaa314908ac2f12ebe06fbdb74213bf63188b, 0x150c93fef652fb1c2bf03e1a29aa871fef77e7d736766c5d0939d92753cc5dc8),
    (0x3270661e68928b3a955d55db56dc57c103cc0a60141e894e14259dce537782b2, 0x073f116f04122e25a0b7afe4e2057299b407c370f2b5a1ccce9fb9ffc345afb3, 0x2a32ec5c4ee5b1837affd09c1f53f5fd55c9cd2061ae93ca8ebad76fc71554d8),
    (0x270326ee039df19e651e2cfc740628ca634d24fc6e2559f22d8ccbe292efeead, 0x27c6642ac633bc66dc100fe7fcfa54918af895bce012f182a068fc37c182e274, 0x1bdfd8b01401c70ad27f57396989129d710e1fb6ab976a459ca18682e26d7ff9),
    (0x162a14c62f9a89b814b9d6a9c84dd678f4f6fb3f9054d373c832d824261a35ea, 0x2d193e0f76de586b2af6f79e3127feeaac0a1fc71e2cf0c0f79824667b5b6bec, 0x044ca3cc4a85d73b81696ef1104e674f4feff82984990ff85d0bf58dc8a4aa94),
    (0x1cbaf2b371dac6a81d0453416d3e235cb8d9e2d4f314f46f6198785f0cd6b9af, 0x1d5b2777692c205b0e6c49d061b6b5f4293c4ab038fdbbdc343e07610f3fede5, 0x2e9bdbba3dd34bffaa30535bdd749a7e06a9adb0c1e6f962f60e971b8d73b04f),
    (0x2de11886b18011ca8bd5bae36969299fde40fbe26d047b05035a13661f22418b, 0x2e07de1780b8a70d0d5b4a3f1841dcd82ab9395c449be947bc998884ba96a721, 0x0f69f1854d20ca0cbbdb63dbd52dad16250440a99d6b8af3825e4c2bb74925ca),
    (0x2eb1b25417fe17670d135dc639fb09a46ce5113507f96de9816c059422dc705e, 0x115cd0a0643cfb988c24cb44c3fab48aff36c661d26cc42db8b1bdf4953bd82c, 0x26ca293f7b2c462d066d7378b999868bbb57ddf14e0f958ade801612311d04cd),
    (0x17bf1b93c4c7e01a2a830aa162412cd90f160bf9f71e967ff5209d14b24820ca, 0x35b41a7ac4f3c571a24f8456369c85dfe03c0354bd8cfd3805c86f2e7dc293c5, 0x3b1480080523c439435927994849bea964e14d3beb2dddde72ac156af435d09e),
    (0x2cc6810031dc1b0d4950856dc907d57508e286442a2d3eb2271618d874b14c6d, 0x25bdbbeda1bde8c1059618e2afd2ef999e517aa93b78341d91f318c09f0cb566, 0x392a4a8758e06ee8b95f33c25dde8ac02a5ed0a27b61926cc6313487073f7f7b),
    (0x272a55878a08442b9aa6111f4de009485e6a6fd15db89365e7bbcef02eb5866c, 0x2d5b308b0cf02cdfefa13c4e60e26239a6ebba011694dd129b925b3c5b21e0e2, 0x16549fc6af2f3b72dd5d293d72e2e5f244dff42f18b46c56ef38c57c311673ac),
    (0x1b10bb7a82afce39fa69c3a2ad52f76d76398265344203119b7126d9b46860df, 0x0f1e7505ebd91d2fc79c2df7dc98a3bed1b36968ba0405c090d27f6a00b7dfc8, 0x2f313faf0d3f6187537a7497a3b43f46797fd6e3f18eb1caff457756b819bb20),
    (0x3a5cbb6de450b481fa3ca61c0ed15bc55cad11ebf0f7ceb8f0bc3e732ecb26f6, 0x3dab54bc9bef688dd92086e253b439d651baa6e20f892b62865527cbca915982, 0x06dbfb42b979884de280d31670123f744c24b33b410fefd4368045acf2b71ae3),
    (0x068d6b4608aae810c6f039ea1973a63eb8d2de72e3d2c9eca7fc32d22f18b9d3, 0x366ebfafa3ad381c0ee258c9b8fdfccdb868a7d7e1f1f69a2b5dfcc5572555df, 0x39678f65512f1ee404db3024f41d3f567ef66d89d044d022e6bc229e95bc76b1),
    (0x21668f016a8063c0d58b7750a3bc2fe1cf82c25f99dc01a4e534c88fe53d85fe, 0x39d00994a8a5046a1bc749363e98a768e34dea56439fe1954bef429bc5331608, 0x1f9dbdc3f84312636b203bbe12fb3425b163d41605d39f99770c956f60d881b3),
    (0x027745a9cddfad95e5f17b9e0ee0cab6be0bc829fe5e66c69794a9f7c336eab2, 0x1cec0803c504b635788d695c61e932122fa43fe20a45c78d52025657abd8aee0, 0x123523d75e9fabc172077448ef87cc6eed5082c8dbf31365d3872a9559a03a73),
    (0x1723d1452c9cf02df419b848e5d694bf27feba35975ee7e5001779e3a1d357f4, 0x1739d180a16010bdfcc0573d7e61369421c3f776f572836d9dab1ee4dcf96622, 0x2d4e6354da9cc554acce32391794b627fafa96fbeb0ab89370290452042d048d),
    (0x153ee6142e535e334a869553c9d007f88f3bd43f99260621670bcf6f8b485dcd, 0x0c45bfd3a69aaa65635ef7e7a430b486968ad4424af83700d258d2e2b7782172, 0x0adfd53b256a6957f2d56aec831446006897ac0a8ffa5ff10e5633d251f73307),
    (0x315d2ac8ebdbac3c8cd1726b7cbab8ee3f87b28f1c1be4bdac9d36a8b7516d63, 0x1b8472712d02eef4cfaec23d2b16883fc9bb60d1f6959879299ce44ea423d8e1, 0x3c1cd07efda6ff24bd0b70fa2255eb6f367d2c54e36928c9c4a5404198adf70c),
    (0x136052d26bb3d373687f4e51b2e1dcd34a16073f738f7e0cbbe523aef9ab107a, 0x16c96beef6a0a848c1bdd859a1232a1d7b3cfbb873032681676c36c24ef967dd, 0x284b38c57ff65c262ab7fed8f499a9fb012387bab4f1662d067eec7f2d6340c4),
    (0x0c5993d175e81f6639e242198897d17cfc06772c1c0411a6af1dff204c922f86, 0x03bf7a3f7bd043dafcda655d1ba9c8f9f24887ad48e17759bbf53f67b1f87b15, 0x3188fe4ee9f9fafbb0cf999567f00e734c8f9cbe69f0e8279b5cd09e36d8be62),
    (0x171f528ccf6584375a39768c480d61e13af5bf77c1c42652afea99a2ec6c595a, 0x12f4175c4ab45afc196e41859b35ef88812c3286ee7000675a0563b9b8e9f1d5, 0x3a509e155cb7ebfd8f8fdcf800a9ac697e23e1aabe96cfab0e74d4d369118b79),
    (0x10f2a685df4a27c81a89920e2504c3b3984bc8f2e4c1b69e98712c65678cfd30, 0x09e5f49790c8a0e21d8d93d54ab91a0e54573c9333c56321e8a16728cc9d4918, 0x352d69bed80ee3e52bf35705d9f84a3442d17ed6ee0fab7e609a740347cf5fea),
    (0x058ee73ba9f3f293491562faf2b190d3c634debd281b76a63a758af6fa84e0e8, 0x232f99cc911eddd9cd0f1fc55b1a3250092cb92119bc76be621a132510a43904, 0x201beed7b8f3ab8186c22c6c5d4869f0f9efd52ca6bc2961c3b97c1e301bc213),
    (0x1376dce6580030c6a1c9291d58602f5129388842744a1210bf6b3431ba94e9bc, 0x1793199e6fd6ba342b3356c38238f761072ba8b02d92e7226454843c5486d7b3, 0x22de7a7488dcc7359fee9c20c87a67df3c66160dc62aacac06a3f1d3b433311b),
    (0x3514d5e9066bb160df8ff37fe2d8edf8dbe0b77fae77e1d030d6e3fd516b47a8, 0x30cd3006931ad636f919a00dabbf5fa5ff453d6f900f144a19377427137a81c7, 0x253d1a5c5293412741f81a5cf613c8df8f9e4b2cae2ebb515b6a74220692b506),
    (0x035b461c02d79d19a35e9613e7f5fe92851b3a59c990fafc73f666cb86a48e8e, 0x23a9928079d175bd5bc00eedd56b93e092b1283c2d5fccde7cfbf86a3aa04780, 0x13a7785ae134ea92f1594a0763c611abb5e2ea3436eef957f1e4ccd73fa00a82),
    (0x39fce308b7d43c574962ae3c0da17e313889c57863446d88bbf04f5252de4279, 0x1aae18833f8e1d3ac0fdf01662f60d22bef00a08c6ed38d23b57e34489b53fad, 0x1a761ce82400af018b2e80c064fd83ed27c1b3fd8f85d8a855513e033398513f),
    (0x275a03e45adda7c316dd1a87ca22e1ccdcf6af2830a502875244ca749b73e481, 0x2e5a10f08b5ab8bbeb08e47e5feabcf807e561453fc5648b58a253cfb6a95786, 0x1459cb8587208473b84e9c333b2932f1c141a5b6d594bec4e033d82cefe78ce3),
    (0x193ae5921d78b5de7b92ce810e14a40052f9332fbffcfbbd5cec7e7b338fbe1b, 0x3097898a5d0011a489111fb2c4660281374384f4a072820560224be67248e82c, 0x378d97bf8c864ae7571782fd96ce54b41979b2d1c465b4d9549980de862930f5),
    (0x2eb04ea7c01d97ec88136287ce376b08dbc7f5cb4609342137ea32a971d17884, 0x36425347ea03f6412302a1c22e49baec861cbda476804e6cead3726f1af2e7b0, 0x26b72df47408ad42cc996cd85c98a1d83f5b5ca5a19a9701ecd627e59590d09e),
    (0x130180e44e2924db1f05636c610b89aade01212ee4588f8959bece31f0a31e95, 0x219e97737d3979ba73275acaed5f579cdf7793cc89e5b52f9ea8e7bc79263550, 0x3cdb93598a5ca5283461363f81c489a23b0672dd7d42cbb49c12635df251d153),
    (0x0e59e6f332d7ed3720724b927a0ca81c4ad0447045a7c5aa2861ce16f219d5a9, 0x1b064342d51a42753d7369467222697a172cc07b9d33fbf943b0a3fcff2036bd, 0x30b82a998cbd8e8a2f363c55b2882e0b78fa9fb9171221b73eb310228a0e5f6c),
    (0x23e4ab37183acba463df7a76e858a4aa8ad71ea715be0573e46f6d4298740107, 0x2795d5c5fa4280225d33094e0beda75bacfe14640de044f2fca995e2b59914a1, 0x3001ca401e89601cd765f26dd03f4c45a6687c3df16c8fe4c26d909dee8b53c0),
    (0x0072e45cc676b08ef7bf86e89280827fe84b5bebae4e501de7fea6bdf3471380, 0x13de705484874bb5e2abe4c518ce599eb64829e2d40e41bdd0c54ddeb26b86c0, 0x0408a9fcf9d61abf315950f1211defe882bb18e5af1b05bb38915b432a9959a5),
    (0x2780b9e75b55676ebb4e4a1400ccd2c4ae4d23b0b41be9a834070cbee26886a0, 0x3a570d4d7c4e7ac3f80333ec85634ac9dc4d8fbefe24405a9405592098b4056f, 0x0c13cca7cb1f9d2cf347c247fcf09294e2cc1507bebdcc6278d2b247899520b4),
    (0x14f59baa03cd0ca4d2614a197c6b794b0b50bb2eb82df74d2e8c88f7707470e0, 0x307defee925dfb436f546e1704c39c60a51d54ede66167f5be52476e0a16f3be, 0x1960cd511a91e0607a07e7674b5a2621661106836adfe5e7380b67d80473dce3),
    (0x2301ef9c63ea84c5ca2ad0fb56672500b8ee335d88284cbe15aaf1f7712589dd, 0x029a5a47da79a488d10f4cd52be97f6bc86182d1b4246b585e68478c4d6027a9, 0x32d7b16a7f11cc962360d17d890e55cbf97fe46b6a9254282cc4f962eaae2260),
    (0x26703e48c03b81ca18e857a98d498cf7a5f2404cd7b35eb0c0cab915d5363d9f, 0x048682a35b3265bc88ac8d25a24603f1f44388bd6b89221ef691123ae112b928, 0x06b1390441fa7030d72cddc6cf06b50791d6e1715164775e3ab7defcb8d803e2),
    (0x31aa0eeb868c626d1689426dce05fcd843b360f6386a86d7bcd795414a6e2e86, 0x239464f75bf7b6af057abad3764c104b90efd8f41b2078b2ed77f5d576b99cc3, 0x0a64d4c04fd426bda45e19ed813a54aba5cc47c59654b2a7b2cb487307c1cecf),
    (0x21fbbdbb73670734576a4ad259860fb1777c7a921a062e9d1f7315322f658735, 0x31b86f3cf01705d4d9371ca2eb95acf35b86d29463d31564674324003fc52146, 0x2bfde53354377c9105ef1736d09056f613541d65157ee1ce7045f48aa4eb4f6f),
    (0x1233ca936ec24671d558f36e65f8eca7f4d5239c11d0eafa5a13a58d20011e2f, 0x27d452a43ac7dea2c437846d8e0b2b30878058d0234a576f6e70af0a7a924b3a, 0x2699dba82184e413e816ea8da493e0fa6a30641a1c3d87b2a02576b94392f980),
    (0x36c722f0efcc8803c3988baee42e4b10f18584664f8cab49608c6f7a61b56e55, 0x02b3ff48861e339b08b0f2ec89ccaa3785c38899a7b5a8336e49ac170dbb7fcd, 0x0b70d061d58d8a7f60162f4427bc657b6fc3ff4c49eb59ada8c5ae03ad98e405),
    (0x3fc2a13f127f96a4f8753adeb9d7cee2ad3de8be46ed96932e06cc4af33b0a06, 0x0c41a6e48dd23a511bd63434ac8c419f00cb3d621e171d80c12080ac117ee15f, 0x2de8072a6bd86884ed4476537169084e72aaad7e4e75339d9685213e9692f5e1),
    (0x03557a8f7b38a17f9d3496a3d9fe05ecb81cf735cc9c39c00ad01184567b027c, 0x0b5f59552f498735ee976d34282f1a37060f43363d818e5445bcb5ac00826abc, 0x0e2923a5fee7b878fedbb18570dc7300f5d646e57507e5482f2909e17e22b0df),
    (0x1d785005a7a00592c787be97020a7fddcf1cb37c3b032af6f71eed73f15b3326, 0x1ad772c273d9c6df0ba5fedcb8f25bd2a590b88a3b0602940acfbfb223f8f00d, 0x027bd64785fcbd2aa78f3275c278234b810510eb61f0672dc1ce13d60f2f5031),
    (0x20800f441b4a0526ce6f8ffea1031b6de224313469457b8e8337f5e07923a853, 0x3d5ad61d7b65f9386eea2cd49f4312b436cdc8eed662ad37a33d7bed89a4408a, 0x13338bc351fc46dd02c5f91be4dd8e3d1df96cc03ea4b26d3bbbae94cc195284),
    (0x25e52be507c92760b87db1e2af3ea923646c49f9b46cbf19c5271c297852819e, 0x1c492d64c157aaa471096d8b1b983c98a34c83a3485c6b2d5c380ab701b52ea9, 0x0c5b801579992718f4e6c5e7a573f592d43487bc288df682a20c0b3da0da4ca3),
    (0x1090b1b4d2bebe7a68695c0cd7cbf43d584e9e62a7f9554e7ea33c93e40833cf, 0x33e38018a801387a68f5ce5cbed19cad1b218e35ecf2328ee383e1ec3baa8d69, 0x1654af18772b2da5eef8d83d0e876bac5f4a02d28729e3aeb76b0b3d787ee953),
    (0x1678be3cc9c6799344742de88c5ab0d5bb0893870367ec6cef7ce6a013265477, 0x3780bd1e01f34c227ff9c6be546e928adaf1818355b13b4faf5d47893348f766, 0x1e83d6315c9f125b0786018e7cb772675d11e69aa6c0b98ca12380320d7cc1de),
    (0x354afd0a2f9d0b26160b41552f2931c8c486894d76e0c33b1799603e855ce731, 0x00cd6d29f166eadc2d8affa62905c5a560b00dbe1faced078b997ee06be1bff3, 0x1d6219352768e3aedbe0e3d7cdbc66efc60d01973f18305708d0641917082f2c),
    (0x146336e25db5181de48d2370d7d1a142afe3ca1db8d4f529fa08dd9806387577, 0x0005d8e085fd72ee997a21163e2e43df022e54b49c13d907a901d3ce84de0ad4, 0x364e97c7a38932270dd5e61c8a4e86426f8ebc1d2296021a1c36f31341964484),
    (0x01189910671bc16b561c6fff15346878fa97ec80ad307a52d7a00c03d2e0baaa, 0x162a7c80f4d2d12e5229dfaa01231a454c0f7e001df490aa63fd8ac57a95ca8c, 0x2a0d6c09576666bb2604e4afb09f8603caff31b4fda3212432e69efb22f40b96),
    (0x0978e5c51e1e5649e16a4d603d5a808ef444d10d63a74e2cc0a0180f8cbfc0d2, 0x1bdcee3aaca9cd25ebe19bbdce25101105087d903bdacfd103f4460ebc351b6e, 0x1862cccb70b5b885e49479140b1944fd0c947321e0075e3ff61964bf3ade7670),
    (0x1f3e91d863c16922bc26cc883a1987e139ee99c1cc6e5ddac3267da6e94adc50, 0x1af47a48a6016a49ef5c08f8478f663afa661465c656ad990f85b4ac2c367406, 0x3c8ee901956e3d3f009d57338c6935051c3698b0a2e3da100eabcd87e7d01b15),
    (0x1660a8cde7fec55368d0b024f591b520e10ce2b7069f4dbd8b94772189673476, 0x0f6d991929d5e4e71303936334dd11323963c2c1f5586e2f9d8d0f67fdaa79d5, 0x02b9cea1921cd9f6cc625eaaab52b4dc4e7fda770712f3437a433091e1ce2d3a),
    (0x14a323b99b900331214f7c6784acb565d8caf468976f04723797b2d8376043b3, 0x190476b580cb9277ec01ea79642d5760718b7fbc7788af78347fef2c00f0953a, 0x090a3a9d869d2eefa42463d30b442b6f9660902b60087651ff4e7e6fb268dfd7),
    (0x3877a955863675670dbe8fd2270a6795e365001304f9a11ef983387ea0456203, 0x2d894691240fe9535df39a2cc63ddc0a60118c53a218135239c0af0fe01f4a06, 0x21b9c18292bdbc597ef71780201661895914e855eeb44aa11aca9eaf9bba9850),
    (0x2fe76be7cff723e2505a05f2a6ae834c272e1cc6c36a296833f509a74ad9d39b, 0x187aa448f391e3ca929981d7cfce253bd15bff840ddae8a50df9fa97277fa8b4, 0x0b7083ad751707bf007ab3aa3617f422663ccf7b2ffe4b5ef0c66af5ffc73736),
    (0x030ddbb470493f163bc4ca9902c52acb1975b962f6cb8e0b2f9b20f1fbd49791, 0x3130fbaffb5aa82a950b0ab18d3546df8fb8ab9d60ea17b23a1c62ca8fbf2525, 0x337f544707c430f04f74d74bac2ee45715ce2ead2fcd051e43a876180dc382e0),
    (0x349979919015394fac9d91b0930dac757d8e471a9fb95fef26de98a8736d1d11, 0x027cc4efe3fb35dd2305cd7a921ec5f13bf93da6fff31d95ccfcb61831d5c775, 0x037f9f2365954c5b61b71a3698682ad267f1c6b7314764afc3fa2629635d27de),
    (0x1f697cac4d07feb710f1cc6df8b4bcd760414abe362d01c977c5b024848371ae, 0x267a750fe5d7cfbc26e6c851fbd572a63145c478063109d6786add244aa0ef29, 0x0c91feab4a43193a678c9996d9a472c8af285fa82ce4fae5180e2b4d3e756f65),
    (0x1745569a0a3e30142186c3038ea05e697e3b83af4a4ba3ba79c47c573ac410f7, 0x29863d546e7e7c0deca5120778a56711fdff66c6f3b5ffe11e0388522696191f, 0x1148d6ab2bd00192bf06bae49ef853f6a79a03df833994c62f225e6366bfe390),
    (0x02e0e121b0f3dfefe18b1499060da366f745f45d350d41d4f4f6331a8b265d15, 0x0d0aa46e76a6a278b89ef73a40a2b274690401736d44a653078ae6aa151054b7, 0x13943675b04aa986eee545f3fa6d3d08392dde710f1f06db9a4d532c7b6e0958),
    (0x2901ec61942d34aad97a11d63088f5d9c9f2b3257530dafe961fc818dcbb66b5, 0x20204a2105d22e7ef431d54434a3e0cf22ffa2a2af9fa3e3fdf544b963d1fdc7, 0x3a8a628295121d5c5c1e3e9e27a571c3a004abe8e01528c41211b9e2190d6852),
)
MDS = (
    (0x0ab5e5b874a68de7b3d59fbdc8c9ead497d7a0ab23850b56323f2486d7e11b63, 0x31916628e58a5abb293f0f0d886c7954240d4a7cbf7357368eca5596e996ab5e, 0x07c045d5f5e9e5a6d803952bbb364fdfa0a3b71a5fb1573519d1cf25d8e8345d),
    (0x233162630ebf9ed7f8e24f66822c2d9f3a0a464048bd770ad049cdc8d085167c, 0x25cae2599892a8b0b36664548d60957d78f8365c85bbab07402270113e047a2e, 0x22f5b5e1e6081c9774938717989a19579aad3d8262efd83ff84d806f685f747a),
    (0x2e29dd59c64b1037f333aa91c383346421680eabc56bc15dfee7a9944f84dbe4, 0x1d1aab4ec1cd678892d15e7dceef1665cbeaf48b3a0624c3c771effa43263664, 0x3bf763086a18936451e0cbead65516b975872c39b59a31f615639415f6e85ef1),
)

# ================================================================ 2 the target hash (reference form: Orchard Poseidon, ConstantLength<2>, 8 full + PARTIAL partial rounds)
CAPACITY = 1 << 65
ROUND_IDX = tuple(range(4)) + tuple(range(4, 4 + PARTIAL)) + tuple(range(60, 64))   # original rounds 0-3 full, 4..PARTIAL+3 partial, 60-63 full
C_UNIT = 216 + 21 * PARTIAL               # C(r) of the cost model: one reference permutation call = C primitive operations


def _round(st, i):
    """Round i of the reference permutation on the state st (list of 3 field elements)."""
    k = ROUND_CONSTANTS[i]
    st = [(st[0] + k[0]) % P, (st[1] + k[1]) % P, (st[2] + k[2]) % P]
    for c in (range(3) if i < 4 or i >= 60 else range(1)):
        st[c] = pow(st[c], 5, P)
    return [(MDS[r][0] * st[0] + MDS[r][1] * st[1] + MDS[r][2] * st[2]) % P for r in range(3)]


def digest(m0, m1):
    """Digest of the Orchard hash of the two canonical field elements (m0, m1): initial state [m0, m1, 2^65], all rounds, output state[0]."""
    st = [m0, m1, CAPACITY]
    for i in ROUND_IDX:
        st = _round(st, i)
    return st[0]


def enc(x):
    """Canonical 32-byte little-endian encoding (x < P)."""
    assert 0 <= x < P
    return x.to_bytes(32, "little")


# ================================================================ 3 the input line and the step program
INV5 = pow(5, -1, P - 1)                  # gcd(5, p - 1) = 1: x -> x^5 is a bijection of the field, with inverse x -> x^INV5


def inv(a):
    return pow(a, P - 2, P)


def root5(a):
    return pow(a, INV5, P)


def line():
    """The input line on which rounds 0 and 1 are affine.  Round 0 maps (m0, m1) to U = (m0 + c00)^5, V = (m1 + c01)^5 (a bijection) and a constant
    third lane; the round-1 S-box input is then affine in (U, V).  On (U, V) = (U0 + a tau, V0 + b tau) its lane 0 is constant (M00 a + M01 b = 0)
    and its lanes 1, 2 are d_i tau, so the S-box gives d_i^5 tau^5: with W = tau^5 the state after round 1 is A + W B.
    message(W) = (U^(1/5) - c00, V^(1/5) - c01) is injective in W (W -> tau -> (U, V) -> (m0, m1), each step injective, a != 0)."""
    kp = pow((CAPACITY + ROUND_CONSTANTS[0][2]) % P, 5, P)
    base = [(MDS[i][2] * kp + ROUND_CONSTANTS[1][i]) % P for i in range(3)]
    a, b = MDS[0][1], (-MDS[0][0]) % P
    det = (MDS[1][0] * MDS[2][1] - MDS[2][0] * MDS[1][1]) % P
    U0 = (-base[1] * MDS[2][1] + base[2] * MDS[1][1]) * inv(det) % P
    V0 = (-MDS[1][0] * base[2] + MDS[2][0] * base[1]) * inv(det) % P
    return a, b, U0, V0


LINE_A, LINE_B, LINE_U0, LINE_V0 = line()


def message(W):
    """The two message elements of the line point W."""
    tau = root5(W)
    return (root5((LINE_U0 + LINE_A * tau) % P) - ROUND_CONSTANTS[0][0]) % P, (root5((LINE_V0 + LINE_B * tau) % P) - ROUND_CONSTANTS[0][1]) % P


def after_round1(m0, m1):
    return _round(_round([m0, m1, CAPACITY], 0), 1)


class Mono:
    """A field element times kappa^e (kappa the attempt's multiplicative coin): value v at kappa = 1, integer exponent e.  Sums are allowed
    only between equal exponents (asserted) or with zero, so every constant built from Monos is exactly K(1) * kappa^e."""
    __slots__ = ("v", "e")

    def __init__(s, v, e=0):
        s.v, s.e = v % P, e

    @staticmethod
    def c(o):
        return o if isinstance(o, Mono) else Mono(o, 0)

    def __mul__(s, o):
        o = Mono.c(o)
        return Mono(s.v * o.v, s.e + o.e)
    __rmul__ = __mul__

    def __add__(s, o):
        o = Mono.c(o)
        if o.v == 0:
            return s
        if s.v == 0:
            return o
        assert s.e == o.e, "sum of different kappa powers"
        return Mono(s.v + o.v, s.e)
    __radd__ = __add__

    def __neg__(s):
        return Mono(-s.v, s.e)

    def __sub__(s, o):
        return s + (-Mono.c(o))

    def __rsub__(s, o):
        return Mono.c(o) + (-s)

    def __mod__(s, m):
        return s

    def __pow__(s, k, m=None):
        if k == P - 2:
            return Mono(pow(s.v, P - 2, P), -s.e)
        return Mono(pow(s.v, k, P), s.e * k)

    def __eq__(s, o):
        return s.v == Mono.c(o).v

    def __ne__(s, o):
        return not s.__eq__(o)

    def __hash__(s):
        return hash((s.v, s.e))

    def at(s, kappa):
        return s.v * pow(kappa, s.e % (P - 1), P) % P


def build_step():
    """The step program: from x (register x) to F(x) = digest(message(x + rho0)) / OUTSCALE (register x), as a straight-line list of
    field operations (op, dest, src1, src2) with op ADD or MUL.  Register names: x (walk value), e0..e2 (attempt registers e_i = E0_i + rho0),
    k<n> (constants, values in the returned dict), y*, z*, h*, u, x5, t1, t2 (working).  Equivalent form of rounds 2..63:
    every lane is held divided by a known nonzero constant scale (one coefficient of each linear combination becomes 1), and the partial rounds
    keep lanes 1, 2 in a basis Q that absorbs the linear layer (only lane 0 and the two update terms are computed).  Returns
    (prog, kval, E0, OUTSCALE)."""
    A = after_round1(*message(0))
    A1 = after_round1(*message(1))
    B = [(A1[i] - A[i]) % P for i in range(3)]
    prog, kval = [], {}

    def K(v):
        name = "k%d" % len(kval)
        kval[name] = v % P if LEV_D else v % P
        return name

    def op(o, d, s, t):
        prog.append((o, d, s, t))

    def pow5(d, s):
        op("MUL", "s_" + d, s, s)
        op("MUL", "s_" + d, "s_" + d, "s_" + d)
        op("MUL", d, "s_" + d, s)

    def mds_norm(sig, cnext, src, dst):
        """dst_i = (sum_j M_ij sig_j src_j + cnext_i) / G_i0 with G = M diag(sig): 2 MUL + 2 ADD (+ 1 ADD for the constant) per lane."""
        lam = []
        for i in range(3):
            G = [MDS[i][j] * sig[j] % P for j in range(3)]
            assert G[0] != 0
            gi = inv(G[0])
            op("MUL", "t1", src[1], K(G[1] * gi))
            op("MUL", "t2", src[2], K(G[2] * gi))
            op("ADD", dst[i], src[0], "t1")
            op("ADD", dst[i], dst[i], "t2")
            if cnext is not None:
                op("ADD", dst[i], dst[i], K(cnext[i] * gi))
            lam.append(G[0])
        return lam

    Y, Z = ["y0", "y1", "y2"], ["z0", "z1", "z2"]
    # round 2: S-box input lane i = A_i + c2_i + (x + rho0) B_i = B_i (x + e_i)
    assert all(B[i] != 0 for i in range(3))
    E0 = [(A[i] + ROUND_CONSTANTS[2][i]) * inv(B[i]) % P for i in range(3)]
    if LEV_D:
        Y = ["x", "y1", "y2"]
        for i in (1, 2):
            op("ADD", Y[i], "x", "e%d" % i)
        sig = [pow(Mono(B[i], 1), 5, P) for i in range(3)]       # lane scales B_i kappa: the program is built once, every constant a Mono
    else:
        for i in range(3):
            op("ADD", Y[i], "x", "e%d" % i)
        sig = [pow(B[i], 5, P) for i in range(3)]
    for i in range(3):
        pow5(Z[i], Y[i])
    Y = ["y0", "y1", "y2"]
    lam = mds_norm(sig, ROUND_CONSTANTS[3], Z, Y)          # round 2 linear layer + round 3 constants
    sig = [pow(l, 5, P) for l in lam]
    for i in range(3):
        pow5(Z[i], Y[i])                                   # round 3 S-boxes
    # round 3 linear layer into the partial-round form: true lane 0 = lam0 h0 + gamma, true lanes (1, 2) = Q (h1, h2) + q.
    # The hidden lanes (h1, h2) = Pm (s1, s2) are held in the basis Pm = diag(nu) M22^PARTIAL, M22 the lower 2 x 2 block of M, so that
    # after the PARTIAL rounds Q = M22^PARTIAL Pm^-1 = diag(nu)^-1 is diagonal; nu_a makes the coefficient of Z0 in h_a equal to 1.
    G = [[MDS[i][j] * sig[j] % P for j in range(3)] for i in range(3)]
    assert G[0][0] != 0
    g0 = inv(G[0][0])
    op("MUL", "t1", Z[1], K(G[0][1] * g0))
    op("MUL", "t2", Z[2], K(G[0][2] * g0))
    op("ADD", "h0", Z[0], "t1")
    op("ADD", "h0", "h0", "t2")
    M22 = [[MDS[1][1], MDS[1][2]], [MDS[2][1], MDS[2][2]]]
    M22r = [[1, 0], [0, 1]]
    for _ in range(PARTIAL):
        M22r = [[(M22[a][0] * M22r[0][b] + M22[a][1] * M22r[1][b]) % P for b in range(2)] for a in range(2)]
    Pm = []
    for a in range(2):
        v = [(M22r[a][0] * G[1][j] + M22r[a][1] * G[2][j]) % P for j in range(3)]    # h_a = nu_a (v . Z)
        assert v[0] != 0
        nu = inv(v[0])
        op("MUL", "t1", Z[1], K(v[1] * nu))
        op("MUL", "t2", Z[2], K(v[2] * nu))
        op("ADD", "h%d" % (1 + a), Z[0], "t1")
        op("ADD", "h%d" % (1 + a), "h%d" % (1 + a), "t2")
        Pm.append([nu * M22r[a][0] % P, nu * M22r[a][1] % P])
    dP = (Pm[0][0] * Pm[1][1] - Pm[0][1] * Pm[1][0]) % P
    assert dP != 0
    dPi = inv(dP)
    Q = [[Pm[1][1] * dPi % P, (-Pm[0][1]) * dPi % P], [(-Pm[1][0]) * dPi % P, Pm[0][0] * dPi % P]]    # Pm^-1: (s1, s2) = Q (h1, h2)
    lam0, gamma = G[0][0], 0
    q = [0, 0]
    for k in range(PARTIAL):
        c = ROUND_CONSTANTS[4 + k]
        op("ADD", "u", "h0", K((gamma + c[0]) * inv(lam0)))
        pow5("x5", "u")
        l5 = pow(lam0, 5, P)
        q = [(q[0] + c[1]) % P, (q[1] + c[2]) % P]
        alpha = MDS[0][0] * l5 % P
        beta = [(MDS[0][1] * Q[0][j] + MDS[0][2] * Q[1][j]) % P for j in range(2)]
        gamma = (MDS[0][1] * q[0] + MDS[0][2] * q[1]) % P
        Qn = [[(MDS[1 + i][1] * Q[0][j] + MDS[1 + i][2] * Q[1][j]) % P for j in range(2)] for i in range(2)]
        q = [(MDS[1 + i][1] * q[0] + MDS[1 + i][2] * q[1]) % P for i in range(2)]
        dt = (Qn[0][0] * Qn[1][1] - Qn[0][1] * Qn[1][0]) % P
        assert alpha != 0 and dt != 0
        di = inv(dt)
        v = [MDS[1][0] * l5 % P, MDS[2][0] * l5 % P]
        w = [(Qn[1][1] * v[0] - Qn[0][1] * v[1]) * di % P, (-Qn[1][0] * v[0] + Qn[0][0] * v[1]) * di % P]   # w = Qn^-1 v
        ai = inv(alpha)
        op("MUL", "t1", "h1", K(beta[0] * ai))
        op("MUL", "t2", "h2", K(beta[1] * ai))
        op("ADD", "h0", "x5", "t1")
        op("ADD", "h0", "h0", "t2")
        op("MUL", "t1", "x5", K(w[0]))
        op("ADD", "h1", "h1", "t1")
        op("MUL", "t2", "x5", K(w[1]))
        op("ADD", "h2", "h2", "t2")
        lam0, Q = alpha, Qn
    # round 60 S-box inputs from the partial-round form, each lane divided by its scale
    c = ROUND_CONSTANTS[60]
    op("ADD", Y[0], "h0", K((gamma + c[0]) * inv(lam0)))
    sig = [pow(lam0, 5, P)]
    assert Q[0][1] == 0 and Q[1][0] == 0 and Q[0][0] != 0 and Q[1][1] != 0     # Q is diagonal after the PARTIAL rounds
    for i in range(2):
        gi = inv(Q[i][i])
        op("ADD", Y[1 + i], "h%d" % (1 + i), K((q[i] + c[1 + i]) * gi))
        sig.append(pow(Q[i][i], 5, P))
    for rnd in (60, 61, 62):
        for i in range(3):
            pow5(Z[i], Y[i])
        lam = mds_norm(sig, ROUND_CONSTANTS[rnd + 1], Z, Y)
        sig = [pow(l, 5, P) for l in lam]
    for i in range(3):
        pow5(Z[i], Y[i])                                   # round 63 S-boxes
    G0 = [MDS[0][j] * sig[j] % P for j in range(3)]        # digest = G0 . z; the step outputs digest / G0[0]
    gi = inv(G0[0])
    op("MUL", "t1", Z[1], K(G0[1] * gi))
    op("MUL", "t2", Z[2], K(G0[2] * gi))
    op("ADD", "x", Z[0], "t1")
    op("ADD", "x", "x", "t2")
    return prog, kval, E0, G0[0]


STEP, KVAL, E0, OUTSCALE = build_step()
if LEV_D:
    KMONO, OUTMONO = KVAL, Mono.c(OUTSCALE)               # constants as monomials in kappa; OUTSCALE_kappa = OUTSCALE_1 kappa^E_OUT
    KVAL = {k: Mono.c(v).v for k, v in KMONO.items()}      # values at kappa = 1
    OUTSCALE, E_OUT = OUTMONO.v, OUTMONO.e
    assert E_OUT == 5 ** (PARTIAL + 6)

    def _terms(e):
        """e = s1 5^a + s2 5^b (s in {-1, 0, 1}, a, b <= PARTIAL + 6): the signed power-of-5 terms, fewest first."""
        if e == 0:
            return ()
        for a in range(PARTIAL + 7):
            for s1 in (1, -1):
                if s1 * 5 ** a == e:
                    return ((s1, a),)
        for a in range(PARTIAL + 7):
            for b in range(PARTIAL + 7):
                for s1 in (1, -1):
                    for s2 in (1, -1):
                        if s1 * 5 ** a + s2 * 5 ** b == e:
                            return ((s1, a), (s2, b))
        raise AssertionError("exponent outside the recipe")
    KTERMS = {k: _terms(v.e) for k, v in KMONO.items()}
    INV_OPS = ((P - 2).bit_length() - 1) + (bin(P - 2).count("1") - 1)     # kappa^-1 by square-and-multiply on p - 2
    # Setup per attempt (D), exact count: kappa^(5^a) and kappa^(-5^a) for a = 1..PARTIAL+6 (3 MUL each), one inversion, one MUL per
    # constant term (K_j(1) times each kappa power of its recipe), e_1, e_2 (one MUL each), and W = kappa x - E0_0 for the two messages
    # (one MUL more each than x + rho0).
    SETUP_D = 2 * 3 * (PARTIAL + 6) + INV_OPS + sum(len(t) for t in KTERMS.values()) + 2 + 2
    # Memory of the setup (D): both power chains (2 (PARTIAL + 7) words), one 16-bit recipe field per constant, E0_1 - E0_0, E0_2 - E0_0,
    # kappa, and 64 setup instructions (4 B each, the format of the step code).
    D_BYTES = 2 * (PARTIAL + 7) * 32 + ((NCONST_D := len(KMONO)) * 2 + 31) // 32 * 32 + 3 * 32 + 64 * 4
else:
    SETUP_D, D_BYTES = 0, 0
OUTINV = inv(OUTSCALE)
NCONST = len(KVAL)                        # step constants, each loaded once per attempt into its own register
REGNAMES = sorted({r for o in STEP for r in o[1:]})
NREG_STEP = len(REGNAMES)                 # registers the step uses: constants, e0..e2, x and working registers
NREG = NREG_STEP + 40                     # + at most 40 control registers of the search (proof.md Section 6 listings): the declared file
_IDX = {r: n for n, r in enumerate(REGNAMES)}
_CODE = tuple((o == "MUL", _IDX[d], _IDX[s], _IDX[t]) for o, d, s, t in STEP)


def kappa_consts(kappa):
    """The attempt's register values for the coin kappa (D): every step constant K_j(1) kappa^(e_j), e_1, e_2, and OUTSCALE_kappa."""
    ki = inv(kappa)
    regs = {name: KMONO[name].at(kappa) for name in KMONO}
    for i in (1, 2):
        regs["e%d" % i] = (E0[i] - E0[0]) * ki % P
    return regs, OUTMONO.at(kappa)


def make_F(rho0):
    """F(x) = digest(message(x + rho0)) / OUTSCALE, computed by executing the step program (every operation of STEP once).
    With D, rho0 is the multiplicative coin kappa and F(x) = digest(message(kappa x - E0_0)) / OUTSCALE_kappa."""
    R = [0] * NREG_STEP
    if LEV_D:
        regs, _ = kappa_consts(rho0)
        for name, v in regs.items():
            R[_IDX[name]] = v
    else:
        for name, v in KVAL.items():
            R[_IDX[name]] = v
        for i in range(3):
            R[_IDX["e%d" % i]] = (E0[i] + rho0) % P
    ix = _IDX["x"]

    def F(x):
        R[ix] = x
        for m, d, s, t in _CODE:
            R[d] = R[s] * R[t] % P if m else (R[s] + R[t]) % P
        return R[ix]
    return F


# ================================================================ 4 the search: one trail, distinguished points, one packed table, recovery
UNROLL = 18                               # trail steps per block
VBITS, GBITS = 142, 119                   # entry = the DP value (x < DELTA < 2^142) and the index gap to the previous stored point (< 2^119)
RBITS = VBITS + GBITS                     # 261 bits per entry, entries packed back to back from bit 0 of the table words
MASK256 = (1 << 256) - 1
# Operation charges (word operations, 1/C each), beside the |STEP| field operations of every evaluation (proof.md Section 6 listings):
W_LOOP = 2        # per trail step, after the step program: CMPLT g, x, DELTA; BZ g, next (skip the inline DP handler)
W_BLOCK = 2       # per block of UNROLL unrolled steps: SUB c, c, UNROLL; BNZ c, block
W_DP = 16         # per distinguished-point event besides scan and insertion, charged at 16 (8 executed): index S - c + slot (2), pointer reset,
                  # call scan, capacity compare, branch, call insert, jump back
W_SCAN = 19       # per table entry examined, charged at 19 (18 executed): word index, bit offset, address (2), two loads (+1 address add),
                  # shift, 255 - offset, two shifts, OR, AND 142-bit mask, compare, branch, pointer add 261, bound compare, branch
W_INS = 40        # per insertion, charged at 40 (37 executed): gap = index - last, compare with 2^119, branch, move; value field and gap field
                  # each a two-word read-modify-write (15 and 16); end pointer add 261; count
W_POS = 24        # per entry walked in the recovery's index passes, charged at 24 (19 and 22 executed): gap field read (14) and index add,
                  # compare with q or record of the previous index, pointer add 261, bound compare, branch
W_REC = 6         # per recovery evaluation beside the step: walk loop 3 (counter, compare, branch); lockstep 11 per 2 evaluations
                  # (move A into x, move result out, the same for B, compare, branch, two moves, counter, compare, branch)
POW_OPS = (INV5.bit_length() - 1) + (bin(INV5).count("1") - 1)   # square-and-multiply for x^INV5: squarings + multiplications
MSG_OPS = 2 * (3 * POW_OPS + 7)           # the two messages: W = A + rho0, tau = W^(1/5), U, V (2 MUL, 2 ADD), two roots, two subtractions


def table_words(m):
    """Words of a table of m packed entries, plus one pad word: every field read loads the word holding its first bit and the next one."""
    return (m * RBITS + 255) // 256 + 1


def _get(tw, off, width):
    """The field of `width` bits at bit offset off (it spans at most two words: off mod 256 + width <= 255 + 142 < 512)."""
    j, sh = off >> 8, off & 255
    return ((tw[j] >> sh) | ((tw[j + 1] << (255 - sh) << 1) & MASK256)) & ((1 << width) - 1)


def _put(tw, off, v):
    """OR the field value v (v < 2^142) into the zeroed bits at bit offset off: two read-modify-writes."""
    j, sh = off >> 8, off & 255
    tw[j] |= (v << sh) & MASK256
    tw[j + 1] |= v >> (255 - sh) >> 1


def search(F, is_dp, x0, steps, mcap, gmax, gpos=None):   # single-gap recovery (credit 43caeb6a Lemma 3 via 1533f8f0): gmax = lockstep cap G, gpos = positioning cap G + d - 1
    """Single-trail collision search on the map F: x_0 = x0, x_i = F(x_{i-1}), UNROLL steps per block.  Every x_i (i >= 1) with is_dp(x_i) is
    stored as one packed entry (x, i - previous stored index); the start x_0 (index 0) is kept in its own word.  Halts (failure) after `steps`
    evaluations (a multiple of UNROLL), when the table already holds `mcap` points at a new one, when an index gap reaches 2^119, or when the
    recovery needs a gap longer than its caps.  When a distinguished value repeats (x_b = x_a, a < b) the trail is periodic from a with period
    L = b - a; the recovery finds the least i with x_i = x_{i+L} and returns (x_{i-1}, x_{i+L-1}), distinct, with F equal on both.
    Returns (pair or None, status, evaluations, ops)."""
    ops = {"trail": 0, "blocks": 0, "rec": 0, "dp": 0, "table": 0, "pos": 0}
    tw = [0] * table_words(mcap)
    cnt, last = 0, 0

    def lookup(x):
        for k in range(1, cnt + 1):
            ops["table"] += W_SCAN
            if _get(tw, (k - 1) * RBITS, VBITS) == x:
                return k
        return None

    x, i, k, b = x0, 0, None, None
    while i < steps and k is None:
        for slot in range(UNROLL):
            x = F(x)
            ops["trail"] += 1
            if is_dp(x):
                ops["dp"] += W_DP
                k = lookup(x)
                if k is not None:
                    b = i + slot + 1
                    break
                if cnt >= mcap:
                    return None, "table", ops["trail"], ops
                ops["table"] += W_INS
                gap = i + slot + 1 - last
                if gap >> GBITS:
                    return None, "gap-width", ops["trail"], ops
                assert x >> VBITS == 0
                _put(tw, cnt * RBITS, x)
                _put(tw, cnt * RBITS + VBITS, gap)
                cnt, last = cnt + 1, i + slot + 1
        if k is None:
            i += UNROLL
            ops["blocks"] += 1
    ev = ops["trail"]
    if k is None:
        return None, "steps", ev, ops
    a, s = 0, 0                             # pass 1: the indices of entries k - 1 and k
    for r in range(1, k + 1):
        ops["pos"] += W_POS
        s, a = a, a + _get(tw, (r - 1) * RBITS + VBITS, GBITS)
    A = x0 if k == 1 else _get(tw, (k - 2) * RBITS, VBITS)      # last stored point before a (index s < mu <= a), or the start
    L = b - a
    q = s + L
    idx, B, cur = 0, x0, 0                  # pass 2: the nearest stored point at or before q, then walk to x_q
    for r in range(1, cnt + 1):
        ops["pos"] += W_POS
        cur += _get(tw, (r - 1) * RBITS + VBITS, GBITS)
        if cur > q:
            break
        idx, B = cur, _get(tw, (r - 1) * RBITS, VBITS)
    if q - idx > (gmax if gpos is None else gpos):
        return None, "gap", ev, ops
    for _ in range(q - idx):
        B = F(B)
        ev += 1
        ops["rec"] += 1
    if A == B:
        return None, "start-on-cycle", ev, ops
    for _ in range(gmax):                   # lockstep: the first index where the two walkers meet
        nA, nB = F(A), F(B)
        ev += 2
        ops["rec"] += 2
        if nA == nB:
            return (A, B), "found", ev, ops
        A, B = nA, nB
    return None, "gap", ev, ops


# ================================================================ 5 the claim's parameters and ledger (derive, plan)
T_DP = 57079                             # a value x is a distinguished point iff x < DELTA = (2^126 + 1) T_DP (T_DP < 2^16, so DELTA < 2^142)
MCAP = 29271                             # table capacity in distinguished points
KD = Fraction(4847, 512)                 # detection window d >= KD / theta_lo, d - 1 >= (KD - 10^-6) / theta_lo; n + d a multiple of UNROLL
H = Fraction(4943, 512)                  # gap cap gmax = G = ceil(H / theta_lo) (the single-gap cap KG)
TAB = 13                                 # table overflow probability <= e^-TAB
STEPS = 169357347293115197307047400440678312334 # S = n + d, the trail length of the attempt: an integer literal, derived offline by `plan` (which asserts it)
GMAXC = 57559123812219353129772389828872039 # gmax = G, the lockstep cap: an integer literal, derived offline by `plan` (which asserts it)
GPOSC = 114000368626669526024776794745024756 # G + d - 1, the positioning cap: an integer literal, derived offline by `plan` (which asserts it)
PREP_OPS = 1 << 58                        # charged bound (word operations) of the offline derivation (`--tune` and `--plan`): proof.md Section 6a
PREP_INSTR = 1 << 14                      # bound on the compiled offline code, in instructions of 4 bytes: proof.md Section 7
PREP_DATA = 1 << 18                       # bound on the data of the offline derivation, in bytes: proof.md Section 7
SMAX = 1 << 128                           # every index of the program is below SMAX (S < 2^128)
GRAIN = 1 << 100                          # n is the least multiple of 2^100 that reaches the success bound
Q_CLAIM = Fraction(39, 100)               # the claimed success probability on the real map (premise H1)
Q_RANDOM = Q_CLAIM                        # the proven success bound on a uniformly random function at the filed budget: the budget is the random-function budget
MISC = 2000 + SETUP_D                     # (D: + the per-attempt constant setup) coins, masks, bounds, halts, counters' setup, two field reads and the report
CODE_OTHER = 600                          # instructions outside the step copies: handlers, scan, insertion, index passes, recovery control, roots, setup loop

# Exact offline arithmetic (integers only: no float, no Decimal, no library function).  A real number v is held as an integer in units of
# 2^-FB (FB = 256).  Every number named below as an upper bound is rounded up, every lower bound down, so each derived inequality is rigorous.
# CNT meters the integer operations of the offline code (add: add, subtract, compare or shift of a multiword value; mul; div: floor division or remainder)
# and the largest operand seen; each routine adds its own statement count (loop bound times operations per iteration, rounded up).  `--tune` prices the
# counts with the prices of the integer routines below (proof.md Section 6a).
FB = 256
ONE = 1 << FB
KEXP = 100                                # terms of the exponential series
KLN = 48                                  # terms of the logarithm series
CNT = {"add": 0, "mul": 0, "div": 0, "bits": 0}

# The integer routines of the offline arithmetic on the word machine of the cost model (proof.md Section 6a).  An integer below 2^IBITS is four 256-bit words
# (little endian).  Word operations, one each: ADD, SUB (mod 2^256), AND, OR, SHL, SHR (by a constant), CMPLT, CMPEQ, a branch, a move, a load, a store.
# `Wm` executes the routines and counts the operations; `--selftest` runs them and asserts that their worst cases are the prices W_IMUL and W_IDIV.
IBITS = 1000                              # every integer of the offline code is below 2^IBITS (the traced maximum is 595 bits)
M256 = (1 << 256) - 1
W_ADD4, W_SH4, W_CMP4 = 14, 10, 13        # four-word add or subtract (carry chain), shift by a constant, comparison: the counts of Wm.add4, shl1, lt4
W_IADD = 32                               # per integer add, subtract, compare or shift: 8 loads + 14, or 8 loads + 13 + a branch, or 4 loads + 10 + 4 stores, at most 32
W_IMUL = 14 + IBITS * (2 + W_ADD4 + 2 * W_SH4 + 2) + 4                          # shift-and-add: per multiplier bit AND, BZ, add, two shifts, SUB, BNZ
W_IDIV = 28 + IBITS * (3 * W_SH4 + 2 + W_CMP4 + 1 + W_ADD4 + 1 + 2) + 8       # restoring division: three shifts, top bit, OR, compare, BNZ, subtract, OR, SUB, BNZ
# Bounds on the offline work other than `--tune` (proof.md Section 6a).  The recipe search `_terms` at its loop bounds: per constant 2 (PARTIAL + 7) iterations of at most
# 12 integer operations and 4 (PARTIAL + 7)^2 iterations of at most 24 (a power 5^a is at most 10 multiplications), each operation priced as a division.  `build_step` and
# the line at their loop bounds: PARTIAL iterations of at most 12 + 100 field operations and 3 inversions (INV_OPS operations each), at most 32 inversions, 6 fifth
# roots (POW_OPS operations each) and 500 field operations elsewhere.  One run of `plan`.
BUILD_OPS = 1 << 17
PLAN_OPS = 1 << 31
RECIPE_OPS = NCONST * (2 * (PARTIAL + 7) * 12 + 4 * (PARTIAL + 7) ** 2 * 24) * W_IDIV
assert PARTIAL * (12 + 100 + 3 * INV_OPS) + 32 * INV_OPS + 6 * POW_OPS + 500 <= BUILD_OPS


class Wm:
    """Counting word machine: every primitive adds one to n; the routines are the offline code's integer operations on four-word integers."""

    def __init__(s):
        s.n = 0

    def ADD(s, a, b): s.n += 1; return (a + b) & M256
    def SUB(s, a, b): s.n += 1; return (a - b) & M256
    def AND(s, a, b): s.n += 1; return a & b
    def OR(s, a, b): s.n += 1; return a | b
    def SHL(s, a, k): s.n += 1; return (a << k) & M256
    def SHR(s, a, k): s.n += 1; return a >> k
    def LT(s, a, b): s.n += 1; return int(a < b)
    def EQ(s, a, b): s.n += 1; return int(a == b)
    def other(s, k=1): s.n += k            # branches, moves, loads and stores

    def add4(s, a, b):                      # a + b, 14 operations
        c = [s.ADD(a[0], b[0])]
        k = s.LT(c[0], a[0])
        for i in (1, 2):
            t = s.ADD(a[i], b[i])
            c.append(s.ADD(t, k))
            k = s.OR(s.LT(t, a[i]), s.LT(c[i], t))
        return c + [s.ADD(s.ADD(a[3], b[3]), k)]

    def sub4(s, a, b):                      # a - b, 14 operations
        c = [s.SUB(a[0], b[0])]
        k = s.LT(a[0], b[0])
        for i in (1, 2):
            t = s.SUB(a[i], b[i])
            c.append(s.SUB(t, k))
            k = s.OR(s.LT(a[i], b[i]), s.LT(t, k))
        return c + [s.SUB(s.SUB(a[3], b[3]), k)]

    def shl(s, a, k):                       # a << k (0 < k < 256), 10 operations
        return [s.SHL(a[0], k)] + [s.OR(s.SHL(a[i], k), s.SHR(a[i - 1], 256 - k)) for i in (1, 2, 3)]

    def shr1(s, a):                         # a >> 1, 10 operations
        return [s.OR(s.SHR(a[i], 1), s.SHL(a[i + 1], 255)) for i in (0, 1, 2)] + [s.SHR(a[3], 1)]

    def lt4(s, a, b):                       # a < b, 13 operations
        lo = [s.LT(a[i], b[i]) for i in range(4)]
        t = lo[0]
        for i in (1, 2, 3):
            t = s.OR(lo[i], s.AND(s.EQ(a[i], b[i]), t))
        return t

    def mul(s, a, b):                       # a * b < 2^IBITS: shift-and-add over IBITS multiplier bits
        s.other(14)                         # 8 loads, 4 zeroing moves, the counter, the constant 1
        c = [0] * 4
        for _ in range(IBITS):
            t = s.AND(b[0], 1)
            s.other()                       # BZ
            if t:
                c = s.add4(c, a)
            a, b = s.shl(a, 1), s.shr1(b)
            s.other(2)                      # SUB, BNZ
        s.other(4)                          # 4 stores
        return c

    def divmod(s, a, b):                    # (a // b, a % b), a < 2^IBITS, b > 0: restoring division over IBITS dividend bits
        s.other(18)                         # 8 loads, 8 zeroing moves, the counter, the constant 1
        a = s.shl(a, 256 * 4 - IBITS)       # the dividend's top bit becomes bit 1023
        r, q = [0] * 4, [0] * 4
        for _ in range(IBITS):
            q = s.shl(q, 1)
            t = s.SHR(a[3], 255)
            a, r = s.shl(a, 1), s.shl(r, 1)
            r[0] = s.OR(r[0], t)
            lt = s.lt4(r, b)
            s.other()                       # BNZ
            if not lt:
                r = s.sub4(r, b)
                q[0] = s.OR(q[0], 1)
            s.other(2)                      # SUB, BNZ
        s.other(8)                          # 8 stores
        return q, r


def words(n):
    return [(n >> (256 * i)) & M256 for i in range(4)]


def number(w):
    return sum(v << (256 * i) for i, v in enumerate(w))


def dp_count(T):
    """Exact count over the field: p = 2^254 + c with c = p mod 2^128 >= T, so exactly (2^126 + 1) * T of the p field elements are distinguished."""
    return ((1 << 126) + 1) * T


def other_fixed(m):
    """Table scans, insertions, the two index passes, constant loads, the message roots, table zeroing (4 per word) and MISC, for m entries."""
    return (m + 1) * (W_DP + W_SCAN * m + W_INS) + 2 * m * W_POS + MSG_OPS + NCONST + 4 * table_words(m) + MISC


def ledger_ops(ops, nstep):
    """Word and field operations of a run, from its counters (nstep = |STEP|)."""
    return ((nstep + W_LOOP) * ops["trail"] + W_BLOCK * ops["blocks"] + (nstep + W_REC) * ops["rec"] + ops["dp"] + ops["table"] + ops["pos"])


def ledger(S, gmax, m, d):
    """The worst-case total (word operations) of the attempt without the preprocessing term: every halt charged at its limit
    (recovery: positioning walk at most gmax + d - 1 evaluations, lockstep at most 2 gmax)."""
    return S * (len(STEP) + W_LOOP) + (S // UNROLL) * W_BLOCK + (3 * gmax + d - 1) * (len(STEP) + W_REC) + other_fixed(m)


def code_instr():
    return UNROLL * (len(STEP) + W_LOOP) + W_BLOCK + (len(STEP) + 20) + NCONST + CODE_OTHER


def fixed_bytes():
    """Bytes of the peak that do not depend on the table size: start word, code, constants, register file, kappa setup."""
    return 32 + code_instr() * 4 + (NCONST + 3 + 8) * 32 + NREG * 32 + D_BYTES


def memory(m=MCAP):
    """Bytes at the peak (the search; setup holds a subset, the offline derivation runs before the attempt): every item is a 32-byte word unless stated."""
    tab = table_words(m) * 32
    consts = (NCONST + 3 + 8) * 32         # step constants, E0, line constants (U0, V0, a, b, c00, c01), INV5, OUTSCALE
    return {"table_words": table_words(m), "table": tab, "start_word": 32, "code_instructions": code_instr(), "code": code_instr() * 4,
            "constants": consts, "registers": NREG, "register_file": NREG * 32, "kappa_setup": D_BYTES, "total": tab + fixed_bytes()}


def exp_neg_ub(xn, xd):
    """Upper bound, in units of 2^-FB, on e^-(xn/xd) for xn/xd >= 0: 1/s with s the floored sum of the first KEXP + 1 terms of the series of e^x,
    a lower bound on e^x (all terms are positive).  Counts: 2 KEXP mul, KEXP + 1 div, KEXP + 2 add."""
    term, s, mx = ONE, ONE, 0
    for k in range(1, KEXP + 1):
        t = term * xn
        mx = max(mx, t.bit_length())
        term = t // (xd * k)
        s += term
    CNT["mul"] += 2 * KEXP + 1            # per term t = term xn and xd k; the final ONE ONE
    CNT["div"] += KEXP + 1                # per term one division; the final one
    CNT["add"] += KEXP + 2                # per term s += term; the final + 1 and the loop bound
    CNT["bits"] = max(CNT["bits"], mx)
    return (ONE * ONE) // s + 1


def exp_consts(KD, H, TAB):
    """(e^-KD, e^-H + e^-(H + KD - 10^-6), e^-TAB) as upper bounds (Lemma 2 (d): lockstep gap and positioning window)."""
    e7 = H + KD - Fraction(1, 10 ** 6)
    CNT["add"] += 4
    return (exp_neg_ub(KD.numerator, KD.denominator), exp_neg_ub(H.numerator, H.denominator) + exp_neg_ub(e7.numerator, e7.denominator),
            exp_neg_ub(TAB, 1))


_EW = {}


def gap_width_ub(T):
    """Upper bound (units 2^-FB) on P(some stored index gap >= 2^GBITS): such a gap holds 2^119 - 1 consecutive indices below t with no DP, hence a
    whole aligned block [j 2^118, (j + 1) 2^118) below t with no DP; at most 2^10 blocks lie below SMAX = 2^128, each empty with probability at
    most (1 - theta_lo)^(2^118) <= e^-(theta_lo 2^118) by Lemma 1 (iii)."""
    if T not in _EW:
        CNT["add"] += 8
        CNT["mul"] += 2
        _EW[T] = (1 << (128 - (GBITS - 1))) * exp_neg_ub((dp_count(T) - SMAX) << (GBITS - 1), P)
    return _EW[T]


def success_fp(n, d, T, ek, c=Fraction(1)):
    """Lower bound (units 2^-FB) on P_F(success) for budget n and detection window d (proof.md Section 5, Lemma 2):
    1 - e^(-c n (n + 1) / 2N) - n / N - eps, eps = e^-KD + n d / N + e^-H + e^-(H + KD - 10^-6) + e^-TAB + E_W, N = p;
    E_W = 2^10 e^-(theta_lo 2^118) bounds an index gap of 2^119 or more (Lemma 2 (e)).
    c = 1 is the random function; other c is the deviation model of Section 8: a uniformly random map on N / c points with the same DP fraction
    theta, so every term that carries 1/N carries c/N and the DP, table and recovery terms keep theta.  Every term of the subtraction is an upper bound.  Returns (bound, eps)."""
    e_kd, e_g, e_tab = ek
    en = exp_neg_ub(c.numerator * n * (n + 1), c.denominator * 2 * P)
    cd_ = c.denominator * P
    nN = (c.numerator * n * ONE + cd_ - 1) // cd_                                 # ceil(c n / N)
    ndN = (c.numerator * n * d * ONE + cd_ - 1) // cd_                            # ceil(c n d / N)
    eps = e_kd + ndN + e_g + e_tab + gap_width_ub(T)
    CNT["mul"] += 10                      # c n (n + 1), 2 c.den P, c.den P, c n ONE, c n d ONE
    CNT["div"] += 2
    CNT["add"] += 12
    CNT["bits"] = max(CNT["bits"], (n * d * ONE).bit_length())
    return ONE - en - nN - eps, eps


def least_k(q, d, T, ek):
    """The least k (n = k 2^100) whose success bound reaches q, by bisection on [2^26, 2^28] (n between 2^126 and 2^128; the bound is below q at the
    lower end and at least q at the upper end, both asserted; the claim needs only that the bound at the returned k reaches q).  At most 30 evaluations."""
    ok = lambda k: success_fp(k * GRAIN, d, T, ek)[0] * q.denominator >= q.numerator * ONE
    lo, hi = 1 << 26, 1 << 28
    assert not ok(lo) and ok(hi)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    CNT["add"] += 150                     # at most 30 evaluations (2 + 28 bisection steps), each with a comparison and a midpoint
    CNT["mul"] += 90                      # k GRAIN and the comparison of each evaluation with q: three products
    CNT["div"] += 28                      # the midpoints
    return hi


def table_exp(S, T, m):
    """Upper bound (units 2^-FB) on ln P(more than m of the stored DPs), by the Chernoff bound of Section 5(c):
    f(mu) = -mu + a (1 + ln(mu / a)), a = m + 1, mu = ceil(S theta_hi) < a, increasing in mu below a; ln(mu / a) <= -(u + u^2/2 + ... + u^KLN / KLN),
    u = 1 - ceil(mu / a) rounded down, since the dropped terms are positive.  Returns (f, mu); f is None if mu >= a."""
    a = m + 1
    mu = (S * dp_count(T) * ONE + (P - SMAX) - 1) // (P - SMAX)
    CNT["mul"] += 3
    CNT["div"] += 1
    CNT["add"] += 12
    CNT["bits"] = max(CNT["bits"], (S * dp_count(T) * ONE).bit_length(), (a * ONE).bit_length() + FB)
    if mu >= a * ONE:
        return None, mu
    u = ONE - (mu + a - 1) // a
    pw, tot = u, 0
    for k in range(1, KLN + 1):
        tot += pw // k
        pw = (pw * u) >> FB
    CNT["mul"] += KLN + 2
    CNT["div"] += KLN + 2
    CNT["add"] += 3 * KLN + 8
    return a * (ONE - tot) - mu, mu


def derive(T, m, KD, H, TAB, q=Q_RANDOM, ek=None):
    """The offline derivation of the trail length S = n + d and the gap cap gmax from T_DP = T and the table size m (integers only)."""
    D = dp_count(T)
    d = -(-(KD.numerator * P) // (KD.denominator * (D - SMAX)))
    d = -(-d // UNROLL) * UNROLL
    gmax = -(-(H.numerator * P) // (H.denominator * (D - SMAX)))
    ek = ek or exp_consts(KD, H, TAB)
    k = least_k(q, d, T, ek)
    n = k * GRAIN
    d += (-(n + d)) % UNROLL              # S = n + d is a whole number of blocks
    while success_fp(n, d, T, ek)[0] * q.denominator < q.numerator * ONE:
        CNT["mul"] += 3
        CNT["div"] += 1
        CNT["add"] += 4
        k += 1
        n = k * GRAIN
        d += (-(n + d)) % UNROLL
    # theta_lo (d - 1) >= KD - 10^-6 (exact), used by Lemma 2 (d)
    assert (D - SMAX) * (d - 1) * 10 ** 6 * KD.denominator >= (KD.numerator * 10 ** 6 - KD.denominator) * P
    CNT["mul"] += 14
    CNT["div"] += 4
    CNT["add"] += 16
    return {"d": d, "gmax": gmax, "n": n, "S": n + d, "ek": ek}


def plan():
    """Offline: re-derives and asserts the literals (STEPS, GMAXC, T_DP < 2^16, the table bound, the memory), then prints the ledger.  Everything
    that fixes a literal or a charge is exact integer arithmetic above; the floats below only format the report (log2 of integers, decimal
    printing) and no literal of the program is computed from them."""
    for key in CNT:
        CNT[key] = 0
    ek = exp_consts(KD, H, TAB)
    r = derive(T_DP, MCAP, KD, H, TAB, Q_RANDOM, ek)
    d, gmax, n, steps = r["d"], r["gmax"], r["n"], r["S"]
    k0 = least_k(Q_CLAIM, d, T_DP, ek)    # the budget at which the random-function bound is 0.39
    n0, k = k0 * GRAIN, n // GRAIN
    succ, eps = success_fp(n, d, T_DP, ek)
    assert succ * Q_RANDOM.denominator >= Q_RANDOM.numerator * ONE
    D_DP = dp_count(T_DP)
    x = n * (n + 1) / (2 * P)             # exponent of the random-function law: P(no repeat in n steps) = e^-x
    lo, hi = 1, 1 << 14                   # the least collision-rate factor c = j / 2^14 at which the bound reaches 0.39 (14 evaluations)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if success_fp(n, d, T_DP, ek, Fraction(mid, 1 << 14))[0] * Q_CLAIM.denominator >= Q_CLAIM.numerator * ONE:
            hi = mid
        else:
            lo = mid
    rate_min = hi / (1 << 14)
    CNT["mul"] += 2 * 20                  # the comparisons of the 14 + 6 evaluations above with 0.39
    rate_table = {str(float(c)): success_fp(n, d, T_DP, ek, c)[0] / ONE for c in (Fraction(1), Fraction(9, 10), Fraction(3, 4), Fraction(3, 5), Fraction(1, 2), Fraction(2, 5))}
    slack = {"n0": n0, "n_over_n0": n / n0, "slack_bits": log2(n / n0), "x": x, "rate_min": rate_min, "rate_table": rate_table}
    assert STEPS is None or (steps == STEPS and gmax == GMAXC and GPOSC == gmax + d - 1), "STEPS, GMAXC, GPOSC are the plan's S, gmax, gmax + d - 1"
    assert steps < SMAX and steps % UNROLL == 0 and T_DP < (1 << 16)
    total_ops = ledger(steps, gmax, MCAP, d) + PREP_OPS
    f, mu = table_exp(steps, T_DP, MCAP)
    assert f is not None and f <= -TAB * ONE      # the table-overflow bound of Section 5(c): mean < MCAP + 1 and ln P(overflow) <= -TAB
    mem = memory()
    assert mem["total"] <= 1 << 20
    prep_peak = fixed_bytes() + 4 * PREP_INSTR + PREP_DATA     # offline code and data (in the table's address range, before the table exists) beside the resident items
    assert prep_peak <= mem["total"]
    ws = len(STEP) + W_LOOP
    tlog = log2(total_ops / C_UNIT)
    assert CNT["bits"] < IBITS
    plan_words = W_IADD * CNT["add"] + W_IMUL * CNT["mul"] + W_IDIV * CNT["div"]
    assert plan_words <= PLAN_OPS
    return {"partial_rounds": PARTIAL, "C": C_UNIT, "step_field_ops": len(STEP), "step_add": sum(o[0] == "ADD" for o in STEP),
            "step_mul": sum(o[0] == "MUL" for o in STEP), "W_LOOP": W_LOOP, "W_BLOCK": W_BLOCK, "W_REC": W_REC,
            "ops_per_trail_step": ws + W_BLOCK / UNROLL, "T_DP": T_DP, "MCAP": MCAP, "KD": str(KD), "H": str(H), "TAB": TAB,
            "theta_log2": log2(D_DP / P), "n": n, "n_over_2^100": k, "n_log2": log2(n), "d": d, "gmax": gmax, "steps": steps,
            "eps_total": eps / ONE, "success_lower_bound": succ / ONE, "success_lower_bound_decimal": "0." + str(succ * 10 ** 20 // ONE).zfill(20),
            "slack": slack, "mean_stored_bound": mu / ONE, "ln_P_table_overflow": f / ONE, "other_fixed": other_fixed(MCAP), "gap_width_bound": gap_width_ub(T_DP) / ONE, "prep_ops": PREP_OPS,
            "prep_log2_units": log2(max(PREP_OPS, 1) / C_UNIT), "total_ops": total_ops,
            "T_units": total_ops / C_UNIT, "time_log2": tlog, "constants": NCONST, "memory": mem,
            "prep_instr": PREP_INSTR, "prep_data_bytes": PREP_DATA, "prep_peak_bytes": prep_peak, "outscale_1": hex(OUTSCALE),
            "plan_integer_ops": {k: CNT[k] for k in ("add", "mul", "div")}, "plan_word_ops": plan_words, "recipe_search_word_ops_bound": RECIPE_OPS}


def tune():
    """Offline: the finite parameter search that fixes the literals T_DP, MCAP, KD, H, TAB and UNROLL.  A cell (U, KD, KG, TAB) takes the largest
    table MCAP with memory <= 2^20 (bisection) and the largest T in [40000, 65535] whose derivation passes the table bound (bisection, 16 probes);
    its value is the exact ledger total.  Descent from (18, 19/2, 77/8, 13): at steps 1/8, 1/64, 1/512, 1/4096, try the 8 (KD, KG) neighbours, U +- 1
    and TAB +- 1, move to any strictly lower total, repeat until no move.  Returns the cell count, the metered integer operations (CNT) and the
    word operations they price to; asserts that the result is the program's literals."""
    global UNROLL
    u0 = UNROLL
    for key in CNT:
        CNT[key] = 0
    cells, mc = [0], {}

    def mcap(U):
        lo, hi = 1, 1 << 17
        while lo < hi:
            mid = (lo + hi + 1) // 2
            CNT["add"] += 24                  # the midpoint, the comparison, and `memory` (table_words, code_instr, fixed_bytes)
            CNT["mul"] += 10
            CNT["div"] += 2
            if memory(mid)["total"] <= 1 << 20:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def cell(U, kd, kg, tab):
        global UNROLL
        UNROLL = U
        if U not in mc:
            mc[U] = mcap(U)
        M = mc[U]
        cells[0] += 1
        ek = exp_consts(kd, kg, tab)

        def feas(T):
            CNT["mul"] += 1
            CNT["add"] += 1
            r = derive(T, M, kd, kg, tab, Q_RANDOM, ek)
            f, mu = table_exp(r["S"], T, M)
            return f is not None and f <= -tab * ONE
        lo, hi = 40000, (1 << 16) - 1
        if not feas(lo):
            return None
        while lo < hi:
            mid = (lo + hi + 1) // 2
            CNT["add"] += 5                   # the midpoint, the loop test, the update
            CNT["div"] += 1
            if feas(mid):
                lo = mid
            else:
                hi = mid - 1
        r = derive(lo, M, kd, kg, tab, Q_RANDOM, ek)
        CNT["add"] += 80                      # the comparison with the best total, and `ledger` with `other_fixed` and `table_words`
        CNT["mul"] += 16
        CNT["div"] += 4
        return ledger(r["S"], r["gmax"], M, r["d"]), (U, kd, kg, tab, lo, M)
    U, kd, kg, tab = 18, Fraction(19, 2), Fraction(77, 8), 13
    best = cell(U, kd, kg, tab)
    for st in (Fraction(1, 8), Fraction(1, 64), Fraction(1, 512), Fraction(1, 4096)):
        moved = True
        while moved:
            moved = False
            cand = [(U, kd + a * st, kg + b * st, tab) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
            for c in cand + [(U - 1, kd, kg, tab), (U + 1, kd, kg, tab), (U, kd, kg, tab - 1), (U, kd, kg, tab + 1)]:
                r = cell(*c)
                if r and r[0] < best[0]:
                    best, moved = r, True
                    U, kd, kg, tab = c
    UNROLL = u0
    assert best[1] == (UNROLL, KD, H, TAB, T_DP, MCAP), best[1]
    words = W_IADD * CNT["add"] + W_IMUL * CNT["mul"] + W_IDIV * CNT["div"]
    offline = words + PLAN_OPS + RECIPE_OPS + BUILD_OPS         # everything offline: this search, one run of `plan`, the recipe search, `build_step`
    assert CNT["bits"] < IBITS and offline < PREP_OPS
    return {"cells": cells[0], "result": [best[1][0], str(best[1][1]), str(best[1][2]), best[1][3], best[1][4], best[1][5]],
            "integer_ops": {k: CNT[k] for k in ("add", "mul", "div")}, "prices": {"add": W_IADD, "mul": W_IMUL, "div": W_IDIV},
            "max_operand_bits": CNT["bits"], "word_ops": words, "offline_word_ops_bound": offline, "offline_log2": log2(offline),
            "word_ops_log2": log2(words), "per_cell_word_ops": words // cells[0], "charged_prep_ops_log2": log2(PREP_OPS)}


def attempt(coin):
    """The claimed attempt (one run, not repeated). It executes only the step program, the table logic and the recovery: STEPS and GMAXC are integer literals (printed with the parameters in section 5), not computed online; `plan` is the offline derivation and check of those literals and of the ledger. coin = two uniformly random 256-bit words; rho0 and x0 are their low 254 bits (every
    254-bit word is below p, so both are canonical). The walk is F(x) = digest(message(x + rho0)) / OUTSCALE. Returns the two 64-byte messages or None."""
    m254 = (1 << 254) - 1
    rho0, x0 = coin[0] & m254, coin[1] & m254
    if LEV_D:
        rho0 = rho0 or 1                  # kappa != 0 (the zero word has probability 2^-254)
    pair, status, ev, ops = search(make_F(rho0), lambda x: x < dp_count(T_DP), x0, STEPS, MCAP, GMAXC, GPOSC)
    if pair is None:
        return None
    (a0, a1), (b0, b1) = (message((rho0 * pair[0] - E0[0]) % P), message((rho0 * pair[1] - E0[0]) % P)) if LEV_D else \
        (message((pair[0] + rho0) % P), message((pair[1] + rho0) % P))
    return enc(a0) + enc(a1), enc(b0) + enc(b1)


# ================================================================ 6 self-checks (reduced width) and command line
NB = 14                                   # walk width of the self-check: the low 14 bits of F (real step program, real rounds)


def run_rho(seed):
    """The search of `attempt` on the reduced map v -> low NB bits of F(v), rho and the start taken from the seed; the pair is checked on the
    reference digest: distinct messages whose digests agree in the low bits that the reduced map keeps (after the division by OUTSCALE)."""
    rho = int(seed, 16) >> 2
    x0 = int(seed[:8], 16) % (1 << NB)
    F = make_F(rho)
    cache = {}

    def F_n(v):
        r = cache.get(v)
        if r is None:
            r = cache[v] = F(v) & ((1 << NB) - 1)
        return r
    pair, status, ev, ops = search(F_n, lambda v: v < (1 << (NB - 4)), x0, 256 - 256 % UNROLL, 64, 160)
    if pair is None:
        return None, {"status": status, "evals": ev, "ops": ops}
    a, b = pair
    if LEV_D:
        rho = rho or 1
        ma, mb = message((rho * a - E0[0]) % P), message((rho * b - E0[0]) % P)
        oi = inv(kappa_consts(rho)[1])
    else:
        ma, mb = message((a + rho) % P), message((b + rho) % P)
        oi = OUTINV
    assert a != b and ma != mb and F_n(a) == F_n(b)
    assert (digest(*ma) * oi % P) & ((1 << NB) - 1) == (digest(*mb) * oi % P) & ((1 << NB) - 1)
    return (ma, mb), {"status": status, "evals": ev, "ops": ops}


ATTEMPT_AND_CHECKS = ("make_F", "search", "attempt", "_get", "_put", "Wm", "words", "number", "run_rho", "offline_nodes", "selftest", "listing", "main")


def offline_nodes():
    """Operator, call and subscript nodes of the offline source: every top-level definition and statement of this file except the attempt (`make_F`, `search`,
    `attempt`, `_get`, `_put`), the word machine and the self-checks.  Proof.md Section 7 bounds the compiled offline code by 8 instructions per node."""
    import ast
    tree = ast.parse(open(__file__, encoding="utf-8").read())
    return sum(isinstance(n, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.Call, ast.Subscript)) for top in tree.body
               if getattr(top, "name", None) not in ATTEMPT_AND_CHECKS for n in ast.walk(top))


def selftest():
    import random
    rng = random.Random(PARTIAL)
    for _ in range(4):                    # the line: rounds 0 and 1 are affine in W, message is injective on samples
        W = rng.randrange(P)
        A, A1, S = after_round1(*message(0)), after_round1(*message(1)), after_round1(*message(W))
        assert all(S[i] == (A[i] + W * (A1[i] - A[i])) % P for i in range(3))
        assert message(W) != message((W + 1) % P)
    for _ in range(6):                    # the step program equals the reference digest of the line message, divided by OUTSCALE
        x, rho0 = rng.randrange(P), rng.randrange(1, 1 << 254)
        if LEV_D:
            _, osk = kappa_consts(rho0)
            assert make_F(rho0)(x) == digest(*message((rho0 * x - E0[0]) % P)) * inv(osk) % P
        else:
            assert make_F(rho0)(x) == digest(*message((x + rho0) % P)) * OUTINV % P
    assert len(STEP) == (135 if LEV_D else 136) + 12 * PARTIAL
    tw, recs, off = [0] * table_words(2000), [], 0     # the packed table at full width: 2000 random entries read back exactly
    for _ in range(2000):
        v, g = rng.randrange(dp_count(T_DP)), rng.randrange(1, 1 << GBITS)
        _put(tw, off, v)
        _put(tw, off + VBITS, g)
        recs.append((v, g))
        off += RBITS
    assert all(_get(tw, j * RBITS, VBITS) == v and _get(tw, j * RBITS + VBITS, GBITS) == g for j, (v, g) in enumerate(recs))
    ok, worst = 0, 0
    for t in range(24):
        res, ob = run_rho(hashlib.sha256(b"t%d" % t).hexdigest())
        ok += res is not None
        o = ob["ops"]
        bound = (len(STEP) + W_LOOP) * 256 + W_BLOCK * 32 + (len(STEP) + W_REC) * 3 * 160 + (64 + 1) * (W_DP + W_SCAN * 64 + W_INS) + 2 * 64 * W_POS
        assert ledger_ops(o, len(STEP)) <= bound and o["trail"] <= 256 and o["rec"] <= 3 * 160
        worst = max(worst, ledger_ops(o, len(STEP)))
    for _ in range(40):                   # the integer routines on the word machine: results equal Python's, counts are within the prices
        a, b = rng.getrandbits(rng.randrange(1, IBITS // 2)), rng.getrandbits(rng.randrange(1, IBITS // 2 - 1))
        m = Wm()
        assert number(m.mul(words(a), words(b))) == a * b and m.n <= W_IMUL
        m = Wm()
        q, r = m.divmod(words(a * b + 7), words(a or 1))
        assert (number(q), number(r)) == divmod(a * b + 7, a or 1) and m.n <= W_IDIV
    full = (1 << IBITS) - 1
    m = Wm()
    assert number(m.mul(words(1), words(full))) == full and m.n == W_IMUL                  # the worst cases are the prices
    m = Wm()
    assert tuple(map(number, m.divmod(words(full), words(1)))) == (full, 0) and m.n == W_IDIV
    for f, w in ((lambda m: m.add4(words(5), words(7)), W_ADD4), (lambda m: m.sub4(words(9), words(7)), W_ADD4), (lambda m: m.shl(words(9), 1), W_SH4),
                 (lambda m: m.shr1(words(9)), W_SH4), (lambda m: m.lt4(words(9), words(7)), W_CMP4)):
        m = Wm()
        f(m)
        assert m.n == w
    assert 8 + W_ADD4 + 4 <= W_IADD and 8 + W_CMP4 + 1 <= W_IADD and 4 + W_SH4 + 4 <= W_IADD
    nodes = offline_nodes()
    assert 8 * nodes + 300 <= PREP_INSTR  # the offline code: 8 instructions per node, plus the three integer routines (at most 300 instructions)
    return {"step_ops": len(STEP), "line_affine": True, "step_equals_reference": 6, "packed_entries_checked": 2000, "rho_n14_pairs": ok, "of": 24, "largest_counted_ops": worst,
            "word_machine_mul": W_IMUL, "word_machine_div": W_IDIV, "offline_nodes": nodes}


def listing():
    return "\n".join("%s %s, %s, %s" % s for s in STEP)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--plan":
            print(json.dumps(plan(), indent=1))
        elif sys.argv[1] == "--selftest":
            print(json.dumps(selftest()))
        elif sys.argv[1] == "--tune":
            print(json.dumps(tune(), indent=1))
        elif sys.argv[1] == "--listing":
            print(listing())
        return
    print(json.dumps(plan(), indent=1))


if __name__ == "__main__":
    main()
