# drone-ltsc2022-support

[Drone-CI](https://www.drone.io/) did not yet publish official docker images compatible with windows `ltsc2022`.

However those images are needed to run windows container with
[`process-isolation`](https://docs.microsoft.com/de-de/virtualization/windowscontainers/manage-containers/hyperv-container)
on self hosted windows 11 workers.

Currently using `ltsc2022` images on a window 11 host is the only viable way to run containers with `process-isolation`, since
[there won't be Window 10 compatible images from microsoft](https://github.com/microsoft/Windows-Containers/issues/117)
and the only other solution would be to not update the windows host system.

This repository's purpose is to build windows `ltsc2022` docker images
and publish them to the github container registry ([ghcr.io](https://ghcr.io/)) until drone has official support for `ltsc2022` images.

For each image the license in the corresponding git submodule applies.
