- Luis Abrie's cat lessong to genie

```
Here's how I get serials on stage \(from `fulfill.py` in the `wp-verify-omg` skill, omg-master\):

1. Only serial-controlled lines need one, meaning products OMG shows with `serialStatusEnabled: Yes` from Oracle's item master \(AI frames, for example\). The item class doesn't decide it.
2. If the FR already recorded serials, from a Flare pick or a lab's Oracle pack, I reuse those.
3. Otherwise I take one per unit from the *facility's OMG pool* in the order's Oracle environment, the same pool `wp-manage-serials` reads. Those are `OMG*`-prefixed serials in that site's stock, like `OMGRS6GQEQJ` and `OMG11300710` that went out on TQVJND00DR at LLAS. When it goes through Oracle, the serial has to come from that facility's own stock.
4. The same serial goes on pick, pack and ship. Each one used gets logged to the run's `serials.jsonl`, so the pool never hands it out twice, since Oracle keeps listing a sold serial until it consumes the unit.
5. You can override with `--serial OMGxxxx`, one per unit. Anything without the `OMG` prefix is refused.

Good luck, Genie. Don't reuse my serials. :black_cat:
```


```
  The place-order lesson for Genie. I read the stored addresses on stage. Nothing was placed.

*Customer and ship-to*
Look them up at `https://account-services-account-api.us-east-1.pvt.gateway.stage.warby.io` with the same Cloudflare Access JWT used for OMG \(`Cf-Access-Jwt-Assertion`\). `/v1/customer/*` is scoped to one customer: always pass `customerID` on the query string. Service-to-service calls also send `x-service-token` \(HS256, `customer_id` matching that query param\). Don't mint or paste that token.

- `GET /v1/customer/?customerID=1890480167793868800`
- `GET /v1/customer/addresses?customerID=...`
- `GET /v1/customer/addresses/:id?customerID=...` \(401 without customerID\)

Copy onto `shippingAddress` as-is: `id`, `firstName`, `lastName`, `streetAddress`, `locality`, `region`, `postalCode`, `countryCode`, `telephone`, `residential`. Use the stored `id`; don't invent one. This customer has four addresses. The one that fits a no-tax online cart is Portland `1957995411067518976`, 1 SW Columbia St, Portland OR 97201. The zip is 97201, not 97204, which is why the earlier check thought Portland was missing. The default is Louisville KY \(taxed — you'd need Vertex tax and a larger payment\).

*Lines, payment, checkout*
Two purchase lines, each stock Alden Pine SRW `19000103`, qty 1, no Rx, no ODF. `configureToOrder.id` is `19000103`, `productId` is `3042041`, `BASE_LENS=SRW`, `priceCents` 19500. Fresh 19-digit `id` and `requestId` per line.

Pay `totals.totalAmount` \(39000 cents for two tax-free $195 lines\) with a saved Visa test card ending 4242 on this customer: `type: saved_credit_card`, `entryType: savedCard`, `ccLastFour: "4242"`. Resolve `ccId` from payment-services; don't invent it or paste a raw card number. Fresh UUID for payment `id`.

`checkoutId` and `referenceOrderId` are the same unused checkout id: `WP` plus 13 characters. Don't reuse one that already placed.

*The call*
There is no separate OMG dry-run place endpoint. Validate the body as a `PlaceOrderRequest`, then `POST https://omg-api.us-east-1.pvt.gateway.stage.warby.io/v1/orders/place_order` with the CF JWT. 201 creates the order\(s\). A 422 persists nothing. Don't POST until Andres says go.

Example \(placeholders in <angle brackets>\). Put two items in `items[]`: copy this line and give the copy its own fresh `id` and `requestId`.

{
  "app": "Web",
  "checkoutId": "<unused WP + 13 chars>",
  "referenceOrderId": "<same checkout id>",
  "referenceSystem": "checkout",
  "userId": "1890480167793868800",
  "userIdType": "customer_id",
  "locale": "US",
  "timezone": "America/New_York",
  "partyId": 1,
  "origin": "Online",
  "suppressEmails": true,
  "customer": {
    "id": "1890480167793868800",
    "email": "ext.agonzalez+1@warbyparker.com",
    "firstName": "Andres",
    "lastName": "Gonzalez",
    "origin": "customer_center",
    "telephone": "8884927297",
    "wantsMarketingEmails": false, "wantsMarketingSms": false,
    "wantsTransactionalEmails": false, "wantsTransactionalSms": false
  },
  "shippingAddress": {
    "id": "1957995411067518976",
    "firstName": "Andres",
    "lastName": "Gonzalez",
    "streetAddress": "1 SW Columbia St",
    "locality": "Portland",
    "region": "OR",
    "postalCode": "97201",
    "countryCode": "US",
    "telephone": "8884927297",
    "residential": true
  },
  "shippingMethod": {"method": "Standard Shipping", "productId": "1"},
  "items": [
    {
      "id": "<fresh 19-digit id>",
      "requestId": "<fresh 19-digit id>",
      "type": "Frame",
      "productId": "3042041",
      "productName": "Alden in Pine",
      "quantity": 1,
      "transactionType": "purchase",
      "configureToOrder": {
        "id": "19000103",
        "price": "195",
        "framePrice": "195",
        "currency": "USD",
        "modelVersion": "glasses-2026-22-04-non-rx-tints",
        "lensConfiguration": [
          {"optionClassId": "BASE_LENS", "optionId": "SRW", "description": "Sun ready-to-wear", "price": "0"}
        ]
      },
      "amounts": {"amount": 19500, "subtotal": 19500, "total": 19500, "currency": "USD", "tax": 0, "adjustmentAmount": 0, "benefitAmount": 0, "copayAmount": 0, "discountAmount": 0, "insuranceAmount": 0, "postTaxAdjustmentAmount": 0, "preTaxAdjustmentAmount": 0, "promotionAmount": 0}
    }
  ],
  "payments": [
    {
      "id": "<fresh uuid>",
      "amount": 39000,
      "currency": "USD",
      "type": "saved_credit_card",
      "ccId": "<this customer's saved Visa 4242 ccId>",
      "ccType": "visa",
      "ccLastFour": "4242",
      "ccExpiresMonth": "<MM>",
      "ccExpiresYear": "<YYYY>",
      "entryType": "savedCard"
    }
  ],
  "totals": {
    "currency": "USD", "subTotal": 39000, "totalAmount": 39000, "taxTotal": 0, "shippingTotal": 0,
    "discountTotal": 0, "promotionsTotal": 0, "adjustmentsTotal": 0, "insuranceTotal": 0, "copayTotal": 0,
    "giftCardTotal": 0, "creditMemoTotal": 0, "cashTotal": 0, "cashDueTotal": 0, "postTaxAdjustmentTotal": 0
  }
}
```


