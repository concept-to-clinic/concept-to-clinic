<template>
  <div class="DICOM-container">
    <div class="DICOM" ref="DICOM"></div>
  </div>
</template>

<script>
  import { EventBus } from '../../main.js'
  var cornerstone = require('cornerstone-core')
  var Q = require('q')

  export default {
    name: 'open-dicom',
    data () {
      return {
        dicom: {
          imageId: '',
          minPixelValue: 0,
          maxPixelValue: 255,
          slope: 1.0,
          intercept: 0,
          windowCenter: 110,
          windowWidth: 100,
          render: cornerstone.renderGrayscaleImage,
          getPixelData: this.getPixelData,
          rows: 512,
          columns: 512,
          height: 512,
          width: 512,
          color: false,
          base64data: '',
          columnPixelSpacing: 1,
          rowPixelSpacing: 1,
          sizeInBytes: 0
        },
        info: null,
        csName: 'LIDC',
        prefixUrl: '/api/images/metadata?dicom_location=/'
      }
    },
    computed: {
      'dicom.sizeInBytes': function () {
        this.dicom.sizeInBytes = this.dicom.rows * this.dicom.columns * 2
      }
    },
    watch: {
      info: function (val) {
        if (val != null) {
          this.applyMeta(val)
          this.loadImage(this.resolveDICOM)
        }
      }
    },
    mounted: function () {
      EventBus.$on('dicom-selection', (path) => {
        this.dicom.imageId = this.csName + ':/' + path
        console.log(this.dicom.imageId)
        this.fetchData(this.dicom.imageId)
      })
    },
    methods: {
      fetchData (id) {
        this.$axios.get(this.prefixUrl + id.slice(this.csName.length + 3))
          .then((response) => {
            this.info = response.data
          })
          .catch(() => {
            // TODO: handle error
          })
      },
      applyMeta (info) {
        var meta = info['metadata']
        this.dicom.base64data = info['image']
        this.dicom.slope = meta['Rescale Slope']
        this.dicom.rows = meta['Rows']
        this.dicom.columns = meta['Columns']
        this.dicom.height = meta['Rows']
        this.dicom.width = meta['Columns']
        this.dicom.columnPixelSpacing = meta['Pixel Spacing']['0']
        this.dicom.rowPixelSpacing = meta['Pixel Spacing']['1']
      },
      str2pixelData (str) {
        var buf = new ArrayBuffer(str.length * 2) // 2 bytes for each char
        var bufView = new Int16Array(buf)
        var index = 0
        for (var i = 0, strLen = str.length; i < strLen; i += 2) {
          var lower = str.charCodeAt(i)
          var upper = str.charCodeAt(i + 1)
          bufView[index] = lower + (upper << 8)
          index++
        }
        return bufView
      },
      getPixelData () {
        var pixelDataAsString = window.atob(this.dicom.base64data)
        var pixelData = this.str2pixelData(pixelDataAsString)
        return pixelData
      },
      resolveDICOM (imageId) {
        var deferred = Q.defer()
        deferred.resolve(this.dicom)
        return deferred.promise
      },
      loadImage (resolve) {
        cornerstone.registerImageLoader(this.csName, resolve)
        var element = this.$refs.DICOM
        console.log(element)

        cornerstone.enable(element)
        console.log(resolve())
        cornerstone.loadImage(this.dicom.imageId).then(function (image) {
          cornerstone.displayImage(element, image)
        })
      }
    }
  }
</script>

<style lang="scss" scoped>
  .DICOM-container {
    width:512px;
    height:512px;
    position:relative;
    display:inline-block;
    color:white;
  }

  .DICOM {
    width:512px;
    height:512px;
    top:0px;
    left:0px;
    position:absolute;
  }
</style>
