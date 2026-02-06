const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {start:"_app/immutable/entry/start.CFfDymgu.js",app:"_app/immutable/entry/app.B3OLRUp4.js",imports:["_app/immutable/entry/start.CFfDymgu.js","_app/immutable/chunks/BiZKocRs.js","_app/immutable/entry/app.B3OLRUp4.js","_app/immutable/chunks/PPVm8Dsz.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./chunks/0-DM_yd7cG.js')),
			__memo(() => import('./chunks/1-B7do7WNY.js')),
			__memo(() => import('./chunks/2-BcDJ5I6-.js').then(function (n) { return n.i; }))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/[...catchall]",
				pattern: /^(?:\/([^]*))?\/?$/,
				params: [{"name":"catchall","optional":false,"rest":true,"chained":true}],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();

const prerendered = new Set([]);

const base = "";

export { base, manifest, prerendered };
//# sourceMappingURL=manifest.js.map
