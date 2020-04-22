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

var routes = new Array();

routes.push({
	path: "/about",
	name: "About Us",
	component: () => import(/* webpackChunkName: "import" */ "@/views/About.vue")
});

export { routes };
