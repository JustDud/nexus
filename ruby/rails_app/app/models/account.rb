# frozen_string_literal: true

module AcmePortal
  # Lightweight stand-in for a Rails model.
  class Account
    attr_reader :id, :name, :status, :created_at

    def initialize(id:, name:, status: "active", created_at: Time.now)
      @id = id
      @name = name
      @status = status
      @created_at = created_at
    end

    def active?
      status == "active"
    end
  end
end
