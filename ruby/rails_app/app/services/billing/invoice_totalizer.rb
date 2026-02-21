# frozen_string_literal: true

module AcmePortal
  module Billing
    # Calculates invoice totals from line items.
    class InvoiceTotalizer
      LineItem = Struct.new(:quantity, :unit_price_cents, keyword_init: true)

      def initialize(line_items:)
        @line_items = line_items
      end

      def subtotal_cents
        @line_items.sum { |item| item.quantity.to_i * item.unit_price_cents.to_i }
      end

      def tax_cents(rate: 0.08)
        (subtotal_cents * rate).round
      end

      def total_cents(rate: 0.08)
        subtotal_cents + tax_cents(rate: rate)
      end
    end
  end
end
