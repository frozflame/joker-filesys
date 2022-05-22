joker-filesys
=============

recent changes
--------------

### version 0.2.0
- add functions `utils.{moves,gen_unique_filename}`
- merge `JointContentAddressedStorage` into `ContentAddressedStorage`
- remove `JointContentAddressedStorage`
- remove `ContentAddressedStorage.{get_path,base_path}`

### version 0.1.5

- add `ContentAddressedStorage.admit()`
- rename `CAS.base_path` => `CAS._base_path`
- rename `CAS.get_path` => `CAS.locate`
- add argument `width` to `spread_by_prefix()`
- fix an integrity issue on `JointContentAddressedStorage`

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
