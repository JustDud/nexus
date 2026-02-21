# frozen_string_literal: true

module AcmePortal
  module Sluggable
    def slug_for(value)
      value.to_s.downcase.strip.gsub(/\s+/, "-").gsub(/[^a-z0-9\-]/, "")
    end
  end
end
