import { expect } from "chai";
import { shallowMount } from "@vue/test-utils";
import PingPong from "@/components/PingPong.vue";

describe("PingPong.vue", () => {
  // Component Contract
  it("submits request to API server when button is clicked", () => {

  });
  it("stores API response message on success", () => {
    const msg = "new message";
    const wrapper = shallowMount(PingPong, {
      propsData: { msg }
    });
    expect(wrapper.text()).to.include(msg);
  });
  it("throws error if API request fails", () => {

  });
  it("throws error if API request exceeds timeout", () => {

  });
  // Snapshot
  it("renders correctly on load", () => {

  });
  it("renders correctly after API response", () => {

  });
});
