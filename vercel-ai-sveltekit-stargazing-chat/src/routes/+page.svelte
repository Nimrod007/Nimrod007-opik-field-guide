<script lang="ts">
  import { Chat } from "@ai-sdk/svelte";

  // @ai-sdk/svelte exposes a Chat class (not a useChat hook). It posts {id, messages} to /api/chat.
  const chat = new Chat({});
  let input = $state("");

  function send(event: SubmitEvent) {
    event.preventDefault();
    if (!input.trim()) return;
    chat.sendMessage({ text: input });
    input = "";
  }
</script>

<main>
  <h1>Nova, your stargazing assistant</h1>
  {#each chat.messages as message (message.id)}
    <p class={message.role}>
      <strong>{message.role === "user" ? "You" : "Nova"}:</strong>
      {#each message.parts as part}{#if part.type === "text"}{part.text}{/if}{/each}
    </p>
  {/each}
  <form onsubmit={send}>
    <input bind:value={input} placeholder="What's up in the sky this month?" />
    <button disabled={chat.status !== "ready"}>Send</button>
  </form>
</main>

<style>
  main { max-width: 40rem; margin: 2rem auto; font-family: system-ui, sans-serif; }
  .user { color: #345; }
  input { width: 70%; padding: 0.4rem; }
</style>
