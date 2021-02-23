# How to Contribute #

## Tools required ##
- Python 3.7.x or 3.8.x (3.8.x is highly recommanded and 3.9 is proscribed).
- Pycharm or Visual Studio code IDE.
- Git.
- UI testing must be done using Chrome latest version.

## Branching ##
### Basic rules ###
- `master` contains only stable releases (which have been merged to `master`) and is intended for end-users.
- `development` is the target for integration and is not intended for end-users.
- `feature` is a temporary feature branch based on `development`.

### Conditions ###
- `master` is not merged back to `development`.
- `development` is not re-based on `master`.
- all `feature` branches branch from `development` only.
- Bugfixes created specifically for a feature branch are done there (because they are specific, they're not cherry-picked to `development`).
- We will not release a patch (0.0.x) if a newer minor (0.x.0) has already been released.


## Typical contribution workflow ##
### Community devs ###
- Fork the repository or pull latest changes if you already have forked it.
- Checkout `development` branch.
- Make the desired changes.
- Submit a PR to Bazarr `development` branch.
- Once reviewed, your PR will be merged using Squash and Merge with a meaningful message.

### Official devs team ###
- All commits must have a meaningful commit message (ex.: Fixed issue with this, Improved process abc, Added input field to UI, etc.).
- Fixes can be made directly to `development` branch but keep in mind that a pre-release with a beta versioning will be created for every push you make.
- Features must be developed in dedicated feature branch and merged back to `development` branch using PR.
- Once reviewed, your PR will be merged using Squash and Merge with a meaningful message.
