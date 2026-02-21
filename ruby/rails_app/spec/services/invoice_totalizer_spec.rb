# frozen_string_literal: true

RSpec.describe AcmePortal::Billing::InvoiceTotalizer do
  it "computes totals from line items" do
    line_items = [
      described_class::LineItem.new(quantity: 2, unit_price_cents: 1500),
      described_class::LineItem.new(quantity: 1, unit_price_cents: 2500)
    ]

    totalizer = described_class.new(line_items: line_items)

    expect(totalizer.subtotal_cents).to eq(5500)
    expect(totalizer.tax_cents(rate: 0.1)).to eq(550)
    expect(totalizer.total_cents(rate: 0.1)).to eq(6050)
  end
end
