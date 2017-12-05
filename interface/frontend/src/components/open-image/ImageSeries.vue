<template>
  <div class="container">

    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            Open imagery
          </div>
          <div class="card-block">
            <template v-if="selected">
              <table class="table table-bordered table-condensed">
                <thead>
                <tr>
                  <th>key</th>
                  <th>value</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="(item, key, index) in selected">
                  <td>{{ key }}</td>
                  <td><small>{{ item }}</small></td>
                </tr>
                </tbody>
              </table>
              <ul>
                <li v-for="el in cases" :key="el.created">
                  <a href="#" @click="selectCase(el)">{{ el.created }}</a>
                  <span v-if="el == selectedCase">&larr;</span>
                </li>
              </ul>
              <button @click="createCase(selected)"
                      class="btn btn-primary float-left case-btn ml-1">
                Create new case
              </button>
              <a href="#/report-and-export"
                 class="btn btn-primary float-left case-btn ml-1">
                Start case
              </a>
            </template>
            <template v-else>
              <p class="card-text">No images imported.</p>
            </template>
          </div>
        </div>
      </div>
    </div><!-- /row1 -->

    <div class="row">
      <div class="col-md-12">
        <div class="card card-outline-warning">
          <div class="card-header">
            Import image series
          </div>
          <div class="card-block pull-left">
            <tree-view class="item pull-left" :model="directories"></tree-view>
            <open-dicom v-show="preview.paths.length" class="pull-right" :view="preview"></open-dicom>
          </div>
        </div>
      </div>
    </div>

  </div><!-- /container -->
</template>

<script>
  import { EventBus } from '../../main.js'
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
        availableSeries: [],
        directories: {
          name: 'root',
          children: []
        },
        preview: {
          type: 'DICOM',
          prefixCS: '://',
          prefixUrl: '/api/images/metadata?dicom_location=/',
          paths: []
        },
        cases: [],
        selectedCase: null,
        selected: null
      }
    },
    watch: {
      selected: function (val) {
        this.cases = []
        this.fetchExistingCases(val)
      },
      'preview.paths': async function (val) {
        if (val.length) {
          const response = await this.$axios.post('api/images/image_series_registration', {
            uri: dirname(this.preview.paths[0])
          })
          if (response.status === 200) this.selected = response.data
        }
      }
    },
    created () {
      this.fetchData()
      this.fetchAvailableImages()
    },
    mounted: function () {
      EventBus.$on('dicom-selection', (path) => {
        this.preview.paths = path
        console.log(this.selected)
      })
    },
    methods: {
      fetchData () {
        this.$http.get('/api/images/')
          .then((response) => {
            this.availableSeries = response.body
          })
          .catch(() => {
            // TODO: handle error
          })
      },
      async fetchExistingCases (series) {
        const response = await this.$axios.post('/api/cases/available', {
          uri: series.uri
        })
        this.cases = response.data
      },
      async createCase (series) {
        console.log(series)
        await this.$axios.post('/api/cases/create', {
          uri: series.uri
        })
        const response = await this.fetchExistingCases(series)
        this.cases = response.data
      },
      selectSeries (series) {
        console.log(series.uri)
        this.selected = series
      },
      selectCase (el) {
        console.log(el.created)
        this.selectedCase = el
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
