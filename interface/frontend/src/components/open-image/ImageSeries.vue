<template>
  <div class="container">
    <div class="offset-top">
      <div class="pt-3">
        <h1> Open Image </h1>
      </div>
      <hr/>
      <div v-if="currentCase">
        <h4>
          You have started this case:
        </h4>

        <table class="table table-bordered table-condensed">
          <tr>
            <td>Patient ID</td>
            <td>{{ currentCase.series.patient_id }}</td>
          </tr>
          <tr>
            <td>Series Instance ID</td>
            <td>
              <small>{{ currentCase.series.series_instance_uid }}</small>
            </td>
          </tr>
        </table>

        <p>
          You can select another DICOM image and start a new case
        </p>
      </div>

      <div class="pt-3">
        <h2> Start a New Case </h2>
      </div>

      <hr/>


      <tree-view class="item pull-left" :model="directories" :open-by-default="true"></tree-view>
      <open-dicom class="pull-right" v-show="preview.paths" :view="preview"></open-dicom>
    </div>

  </div>

</template>

<script>
  import {EventBus} from '../../main.js'
  import TreeView from './TreeView'
  import OpenDicom from './OpenDICOM'
  import dirname from 'path-dirname'

  export default {
    components: {
      TreeView,
      OpenDicom
    },
    data () {
      return {
        directories: {
          name: 'root',
          children: []
        },
        preview: {
          type: 'DICOM',
          prefixCS: '://',
          prefixUrl: '/api/images/metadata?dicom_location=/',
          paths: null
        },
        currentCase: null
      }
    },
    created () {
      this.fetchData()
      this.fetchAvailableImages()
    },
    mounted: function () {
      EventBus.$on('dicom-selection', (paths) => {
        this.preview.paths = paths
      })

      EventBus.$on('start-new-case', (filePath) => {
        if (!this.currentCase || confirm('This will drop the current case and start a new one. Are you sure?')) {
          // drop the current case and start a new one
          this.$axios.post('api/cases/start_new_case', {
            uri: dirname(filePath)
          }).then((response) => {
            if (response.status === 200) {
              this.currentCase = response.data
            }
          })
        }
      })
    },
    methods: {
      fetchData () {
        this.$http.get('/api/cases/')
            .then((response) => {
              this.currentCase = response.body[0]
            })
            .catch(() => {
              // TODO: handle error
            })
      },
      fetchAvailableImages () {
        this.$http.get('/api/images/available')
            .then((response) => {
              this.directories = response.body.directories
            })
            .catch(() => {
              // TODO: handle error
            })
      }
    }
  }
</script>
