<template>
    <div>
        <div class="button" style="display:inline-block" @click="pingServer">{{ msg }}</div>
    </div>
</template>

<script>
import axios from "axios";

export default {
    name: "Ping",
    methods: {
        pingServer: function() {
			const path = "http://localhost:5000/ping";
            axios
                .get(path)
                .then(res => {
                    this.msg = res.data;
					console.log("promise resolved! ("+this.msg+")")
                })
                .catch(error => {
                    if (process.env.NODE_ENV !== "production") {
                        console.error("SENT ['"+error.request.method+"','"+error.request.url+"']")
                        console.error(error.message);
                    }
                    if (error.response.status == "408") {       // 408 Request Timeout
                        // Unable to reach API server (check your internet connection, retrying in?)

                    } else if (error.response.status == "404") {        // 404 Not Found
                        // API entrypoint invalid

                    } else {
                        // Unexpected error. Please Try again later.

                    }
				});
        }
    },
    data() {
        return {
            msg: "Ping"
        };
    }
};
</script>
