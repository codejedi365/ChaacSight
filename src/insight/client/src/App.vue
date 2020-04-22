<template>
  <div id="app">
    <div id="nav">
      <router-link
        v-for="(link, iLink) in sortedRouteLinks"
        :key="iLink"
        :to="link.path"
        :class="iLink != 0 ? 'preSpacer' : ''"
        >{{ link.text }}</router-link
      >
    </div>
    <router-view />
  </div>
</template>

<script>
import { default as features } from "@/utils/features";

export default {
    name: "App",
    computed: {
        routeLinks: function() {
            return this.routes.filter(function(rt) {
                return !(features["route"][rt.path] === false);
            });
        },
        sortedRouteLinks: function() {
            var lightest2Heaviest = (a, b) => {
                return a.weight < b.weight ? -1 : a.weight > b.weight ? 1 : 0;
            };
            var sortedLinks = Array.from(this.routeLinks).sort(lightest2Heaviest);
            return sortedLinks;
        }
    },
    data() {
        return {
            features: features,
            routes: [
                // { path: "", text: "", hover: "", weight: 0, subroutes: null },
                { path: "/", text: "Home", hover: "", weight: 0, subroutes: null },
                { path: "/about", text: "About", hover: "", weight: 10, subroutes: null },
                { path: "/data/import", text: "Import Data", hover: "", weight: 5, subroutes: null }
            ]
        };
    }
};
</script>

<style lang="scss">
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

#nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: #2c3e50;

    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
.preSpacer::before {
    content: " | ";
}
</style>
