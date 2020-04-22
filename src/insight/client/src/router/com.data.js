/**
 * 
 * 
 * DEFINING Routes (2 methods):
 * 1. webpack's route level code-splitting for lazy-loading
 *    this generates a separate chunk (about.[hash].js) for this route
 *    if and only if the route is visited, then the chunk is loaded.
 * 2. Import at top of this page and then directly specify the component
 *    example is "Home" below.
 */
import { default as features } from "@/utils/features";

var routes = new Array();

if (features["route"]["/data/import"] || false) {
	routes.push({
		path: "/data/import",
		name: "Import",
		component: () => import(/* webpackChunkName: "import" */ "@/views/ImportData.vue")
	});
}

export { routes };
