<template>
<div class="container">
  <wizard-flow :steps="steps">
    <image-series slot="main-content"></image-series>
  </wizard-flow>
</div>
</template>

<script>
import {
  mapGetters
} from 'vuex'

import WizardFlow from '../components/common/WizardFlow'
import ImageSeries from '../components/open-image/ImageSeries'

export default {
  name: 'open-image',
  components: {
    ImageSeries,
    WizardFlow
  },
  computed: {
    ...mapGetters({
      imageInProgress: 'imageInProgress',
      candidatesExist: 'candidatesExist'
    }),
    steps () {
      return [{
        name: 'Select a Case or Import Imagery',
        active: this.candidatesExist || this.imageInProgress.id
      },
      {
        name: 'Create a new Case',
        active: this.imageInProgress.id && this.imageInProgress.caseCreated
      },
      {
        name: 'Case is Ready',
        active: this.candidatesExist
      }]
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
