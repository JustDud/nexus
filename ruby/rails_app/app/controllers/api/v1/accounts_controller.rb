# frozen_string_literal: true

module AcmePortal
  module Api
    module V1
      # Minimal API controller example.
      class AccountsController
        def index
          []
        end

        def show(id:)
          { id: id, name: "Example Account" }
        end
      end
    end
  end
end
