joker-filesys
=============

recent changes
--------------

### version 0.1.4

- add `JointContentAddressedStorage`
- deprecate `ContentAddressedStorage.base_path`
- add `utils.compute_collision_probability()`
- add `utils.{PathLike,FileLike}`

### version 0.1.3

- add `utils.spread_by_prefix` and `utils.random_hex`

### version 0.1.2

- python_requires >= 3.6
- change `ContentAddressedStorage.hash_algo` default value to `sha256`
- add `ContentAddressedStorage._iter_{paths,cids}`
- naming: key => cid

### version 0.1.1

- add `ContentAddressedStorage`
