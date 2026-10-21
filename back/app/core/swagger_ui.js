/* Presentation-only cURL examples for Swagger UI 5.34.0. */
(function () {
  "use strict";

  window.FoodifySwaggerCurlPlugin = function (system) {
    const createElement = system.React.createElement;

    function requiresBearerToken(selectors, path, method) {
      const operation = selectors.operationWithMeta(path, method);
      const requirements = operation.get("security", selectors.security());
      return requirements.some(function (requirement) {
        return requirement.has("BearerAuth");
      });
    }

    function createDisplayRequest(request) {
      let headers = request.get("headers") || system.Im.Map();
      const acceptKey = headers.findKey(function (_, name) {
        return name.toLowerCase() === "accept";
      });
      const authorizationKey = headers.findKey(function (_, name) {
        return name.toLowerCase() === "authorization";
      });
      const accept = acceptKey === undefined ? null : headers.get(acceptKey);

      if (!accept || accept === "*/*") {
        headers = headers.set(acceptKey || "accept", "application/json");
      }
      if (!authorizationKey || !headers.get(authorizationKey)) {
        headers = headers.set(
          authorizationKey || "Authorization",
          "Bearer ACCESS_TOKEN_HERE"
        );
      }

      // Immutable copies are used only by the snippet renderer, never by fetch.
      return request.set("headers", headers);
    }

    function CurlExample(props) {
      const request = createDisplayRequest(props.request);
      let snippet = system.fn.requestSnippetGenerator_curl_bash(request);
      if (request.get("method") === "GET") {
        snippet = snippet.replace(/^curl -X 'GET' \\\n  /, "curl ");
      }
      const HighlightCode = props.getComponent("HighlightCode", true);

      return createElement(
        "div",
        { className: "curl-command" },
        createElement("h4", null, "Curl"),
        createElement(
          HighlightCode,
          { language: "bash", canCopy: true },
          snippet
        )
      );
    }

    return {
      wrapComponents: {
        liveResponse: function (Original) {
          return function (props) {
            if (!requiresBearerToken(props.specSelectors, props.path, props.method)) {
              return createElement(Original, props);
            }

            const getComponent = function (name, container, configuration) {
              if (name === "curl") {
                return function (curlProps) {
                  return createElement(CurlExample, {
                    ...curlProps,
                    getComponent: props.getComponent,
                  });
                };
              }
              return props.getComponent(name, container, configuration);
            };

            return createElement(Original, { ...props, getComponent: getComponent });
          };
        },
      },
    };
  };
})();
