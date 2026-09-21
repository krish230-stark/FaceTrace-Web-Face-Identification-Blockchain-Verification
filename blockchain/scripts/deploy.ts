import { network } from "hardhat";

const { viem } = await network.connect({
  network: "sepolia",
});

const postVerifier = await viem.deployContract("PostVerifier");

console.log(
  "PostVerifier deployed to:",
  postVerifier.address
);