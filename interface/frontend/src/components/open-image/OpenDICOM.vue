<template>
  <div class="container">
    <div class="col-xs-6">
      <div class="DICOM-container">
        <div class="DICOM" ref="DICOM"></div>
      </div>
      <p>{{ dicom.imageId}}</p>>
    </div>
  </div>
</template>

<script>
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
          windowCenter: 90,
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
          sizeInBytes: 512 * 512 * 2
        },
        dicomUrl: 'LIDC://LIDC-IDRI-0001/1.3.6.1.4.1.14519.5.2.1.6279.6001.298806137288633453246975630178/1.3.6.1.4.1.14519.5.2.1.6279.6001.179049373636438705059720603192/-95.000000.dcm',
        info: null,
        csName: 'LIDC'
      }
    },
    watch: {
      info: function (val) {
        if (val != null) {
          this.applyMeta(val)
          console.log(this.dicom)
          this.loadImage(this.resolveDICOM)
        }
      }
    },
    mounted: function () {
      this.fetchData(this.dicomUrl)
    },
    methods: {
      fetchData (id) {
        this.$axios.get('/api/images/metadata?dicom_location=/images/' + id.slice(this.csName.length + 3))
          .then((response) => {
            this.info = response.data
          })
          .catch(() => {
            // TODO: handle error
          })
      },
      applyMeta (info) {
        this.dicom.imageId = this.dicomUrl
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
        cornerstone.registerImageLoader('LIDC', resolve)
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
