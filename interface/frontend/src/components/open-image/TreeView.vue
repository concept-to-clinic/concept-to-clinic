<template>
  <ul>
    <li>
      <span @click="toggle" v-if="isOpenable">
        <span v-bind:class="{'font-weight-bold': isOpen && isViewable}">
          {{ model.name }}
        </span>
        <span v-if="isViewable">
          <i v-if="!isOpen" class="fa fa-eye"></i>
        </span>
        <span v-else>
           [{{isOpen ? '-' : '+'}}]
        </span>
      </span>
      <span v-else>
        {{ model.name }}
      </span>
      <div v-show="isOpen">
        <ul v-if="isFolder">
          <tree-view class="item"
                     v-for="child in model.children"
                     v-if="child.children"
                     :key="child.name"
                     :model="child"
          ></tree-view>
        </ul>
        <button @click="startNewCase" v-if="isViewable" class="btn btn-sm btn-primary" role="button">
          Start New Case
        </button>
      </div>
    </li>
  </ul>
</template>


<script>
  import TreeView from './TreeView'
  import {EventBus} from '../../main.js'

  export default {
    name: 'tree-view',
    props: {
      model: {
        type: Object,
        default: {
          'name': 'root',
          'children': [],
          'files': [],
          'type': 'folder'
        }
      },
      openByDefault: {
        type: Boolean
      }
    },
    components: {
      TreeView
    },
    data () {
      return {
        // open single-item-folders by default
        isOpen: this.openByDefault || this.model.children && this.model.children.length === 1
      }
    },
    created () {
      EventBus.$on('dicom-selection', () => {
        if (this.isViewable) {
          this.isOpen = false
        }
      })
    },
    computed: {
      isFolder () {
        return this.model.type === 'folder'
      },
      hasContents () {
        return this.isViewable || this.hasFolders
      },
      hasFolders () {
        if (this.model.children) return this.model.children.length > 0
        return false
      },
      isViewable () {
        if (this.model.files) return this.model.files.length > 0
        return false
      },
      isOpenable () {
        return this.isFolder && this.hasContents
      }
    },
    methods: {
      toggle: function () {
        const opening = !this.isOpen

        if (this.isViewable) {
          if (opening) {
            // open the viewer on expanding the last folder
            EventBus.$emit('dicom-selection', this.model.files.map((file) => {
              return file.path
            }))
          } else {
            // close the viewer on collapsing the folder
            EventBus.$emit('dicom-selection', null)
          }
        }

        this.isOpen = opening
      },
      startNewCase () {
        // start selected folder as a new case
        EventBus.$emit('start-new-case', this.model.files[0].path)
      }
    }
  }
</script>

<style lang="scss" scoped>
  .item {
    cursor: pointer;
  }

  .bold {
    font-weight: bold;
  }

  ul {
    padding-left: 1em;
    line-height: 1.5em;
    list-style-type: dot;
  }
</style>
