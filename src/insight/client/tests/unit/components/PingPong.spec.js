import { assert } from "chai";
import sinon from "sinon";
import { shallowMount } from "@vue/test-utils";
import flushPromises from "flush-promises";
import PingPong from "@/components/PingPong.vue";

const apiURL = "http://localhost:5000";
var sinonServer;

describe("PingPong.vue", () => {
    const requestPairs = [
        { [ [apiURL, "ping"].join("/") ]: "Pong" },
    ]

    beforeEach(() => {
        sinonServer = sinon.fakeServer.create();
        sinonServer.respondImmediately = true;
        // sinonServer.respondWith([apiURL, "ping"].join("/"), "Pong")
        // requestPairs.forEach(item => {
        //     var url = Object.keys(item)[0];
        //     sinonServer.respondWith(url,item[url]);
        // },this);
    });
    afterEach(() => {
        sinonServer.restore();
        // Restore the default sandbox here
        sinon.restore();
    });

    // Component Contract
    it("submits request to API server when button is clicked", async () => {
        sinonServer.respondWith("GET", [apiURL, "ping"].join("/"), "Pong")
        assert.strictEqual(sinonServer.requests.length, 0, 'No request yet');

        const wrapper = shallowMount(PingPong);
        wrapper.get("div.button").trigger("click");
        await flushPromises();

        assert.strictEqual(sinonServer.requests.length, 1, 'Only one request');
		assert.strictEqual(sinonServer.requests[0].url, [apiURL, "ping"].join("/"), 'correct API URL');
    });
    it("stores API response message on success", async () => {
        const responseMsg = "Pong";
        sinonServer.respondWith("GET", [apiURL, "ping"].join("/"), responseMsg)

        const wrapper = shallowMount(PingPong);
        assert.notEqual(wrapper.vm.msg, responseMsg);

        wrapper.get("div.button").trigger("click");
        await flushPromises();

        assert.equal(wrapper.vm.msg, responseMsg);
    });
    it("throws error if API request fails", async () => {
        // no server path set up so default is 404 error

        // replace the console.log since this will throw an axios super error
        // const fakeConsole = sinon.fake();
        // sinon.replace(console, "error", fakeConsole)

        const wrapper = shallowMount(PingPong);
        // assert.equal(wrapper.vm.??,0,'No errors yet')

        wrapper.get("div.button").trigger("click");
        await flushPromises();

        assert.fail("Test 50% Implemented")
        // assert.equal(wrapper.vm.??, 1, '1 error found');
    });
    /*
    it("throws error if API request exceeds timeout", () => {
        assert.fail("Test Not Implemented");
    });
    // Snapshot
    it("renders correctly on load", () => {
        assert.fail("Test Not Implemented");
    });
    it("renders correctly after API response", () => {
        assert.fail("Test Not Implemented");
    });*/
});
