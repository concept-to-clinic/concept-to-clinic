<template>
  <div class='row'>
    <div class='col-md-3 floating-list-container'>
      <ul class='floating-list'>
        <li v-for='{name, active} in steps'
            :class="{
                'active' : active
              }">
            {{ name }}
        </li>
      </ul>
    </div>
    <div class='col-md-9'>
      <slot name="main-content"></slot>
    </div>
  </div>
</template>

<script>

export default {
  props: ['steps'],
  computed: {
    ...this.stepMapGetters
  }
}
</script>

<style lang="scss" scoped>
p label {
    font-weight: bold;
}

.floating-list-container {
  max-width: 270px;
}

.floating-list {
    list-style: none;
    margin-top: 0;
    padding: 0;

    display: flex;
    flex-direction: column;
    justify-content: space-around;
    align-items: flex-start;

    position: fixed;

    height: 90vh;
    width: inherit;
    max-width: inherit;

    li {
        padding: 0.5em;
        height: 4em;
        background-color: #383B42;
        border-bottom: 1px solid #2E3036;
        transition: 0.6s;

        font-size: 1.20em;

        text-decoration: none;

        line-height: 1em;

        display: flex;
        align-items: center;

        position: relative;
        letter-spacing: 1px;
        transition: all 0.6s;
        color: #b3b3b3;

        &:hover {
            cursor: pointer;
            background-color: #454952;
            color: #fff;
        }

        &.active {
            box-shadow: 5px 0 5px rgba(0, 0, 0, 1);
            background-color: white;
            color: black;
        }
    }
}
</style>
