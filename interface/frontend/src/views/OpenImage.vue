<template>
  <div class="container">
    <image-series></image-series>
    <open-dicom></open-dicom>
  </div>
</template>

<script>
import ImageSeries from '../components/open-image/ImageSeries'
import OpenDicom from '../components/open-image/OpenDICOM'

export default {
  components: {
    ImageSeries,
    OpenDicom
  },
  name: 'open-image'
}
</script>

<style lang="scss" scoped>
</style>
